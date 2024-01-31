import json
import logging
import os
from typing import Type
from clddp.dm import LabeledQuery, RetrievedPassageIDList
from clddp.utils import initialize_ddp, is_device_zero, parse_cli, set_logger_format
from dapr.retrievers.dense import JinaV2
from dapr.exps.jinav2_doc_passage_fusion.args.base import (
    JinaV2DocPassageFusionArguments,
)
from dapr.dataloader import DAPRDataConfig, DAPRDataLoader, RetrievalLevel
from clddp.evaluation import RetrievalEvaluator
from clddp.search import search
from dapr.fusion import doc_passage_fusion_with_M2C2
import numpy as np
import tqdm
from matplotlib import pyplot as plt


def run_jina_doc_passage_fusion(
    arguments_class: Type[JinaV2DocPassageFusionArguments], passage_retriever_name: str
) -> None:
    set_logger_format(logging.INFO if is_device_zero() else logging.WARNING)
    initialize_ddp()
    args = parse_cli(arguments_class)
    if is_device_zero():
        args.dump_arguments()

    # Doing JinaV2 document retrieval:
    fdocs_ranking = os.path.join(args.output_dir, "doc_ranking_results.txt")
    doc_dataset = DAPRDataLoader(
        DAPRDataConfig(
            data_name_or_path=args.data_dir, retrieval_level=RetrievalLevel.document
        )
    ).load_data(is_device_zero())
    labeled_queries = doc_dataset.get_labeled_queries(args.split)
    queries = LabeledQuery.get_unique_queries(labeled_queries)
    retriever = JinaV2()
    retrieved_docs = search(
        retriever=retriever,
        collection_iter=doc_dataset.collection_iter,
        collection_size=doc_dataset.collection_size,
        queries=queries,
        topk=args.topk,
        per_device_eval_batch_size=args.per_device_doc_batch_size,
        fp16=args.fp16,
    )
    if is_device_zero():
        RetrievedPassageIDList.dump_trec_csv(
            retrieval_results=retrieved_docs, fpath=fdocs_ranking, system="jinav2"
        )
        logging.info(f"Saved JinaV2 document ranking results to {fdocs_ranking}.")

    # Loading passage ranking results and doing fusion:
    if is_device_zero():
        retrieved_passages = RetrievedPassageIDList.from_trec_csv(args.passage_results)
        paragraph_dataloader = DAPRDataLoader(
            DAPRDataConfig(
                data_name_or_path=args.data_dir,
                retrieval_level=RetrievalLevel.paragraph,
            )
        )
        pid2did = paragraph_dataloader.get_pid2did(is_device_zero())
        passage_weights = [
            round(weight, 1) for weight in np.arange(0, 1.1, 0.1).tolist()
        ]
        paragraph_dataset = paragraph_dataloader.load_data(is_device_zero())
        pwegiht2metrics = {}
        for passage_weight in tqdm.tqdm(passage_weights, desc="Doing fusion"):
            fused = doc_passage_fusion_with_M2C2(
                doc_results=retrieved_docs,
                passage_results=retrieved_passages,
                pid2did=pid2did,
                passage_weight=passage_weight,
            )
            evaluator = RetrievalEvaluator(
                eval_dataset=paragraph_dataset, split=args.split
            )
            report = evaluator(fused)
            pwegiht2metrics[passage_weight] = report
            freport = os.path.join(
                args.output_dir, f"metrics-pweight_{passage_weight}.json"
            )
            with open(freport, "w") as f:
                json.dump(report, f, indent=4)
            logging.info(f"Saved evaluation metrics to {freport}.")
            franked = os.path.join(
                args.output_dir, f"ranking_results-pweight_{passage_weight}.txt"
            )
            RetrievedPassageIDList.dump_trec_csv(
                retrieval_results=fused, fpath=franked, system=passage_retriever_name
            )
            logging.info(f"Saved ranking results to {franked}.")

        # Save again the metrics to be reported:
        if args.report_passage_weight:
            report_metrics = pwegiht2metrics[args.report_passage_weight]
            freport = os.path.join(args.output_dir, f"metrics.json")
            with open(freport, "w") as f:
                json.dump(report_metrics, f, indent=4)
            logging.info(f"Saved evaluation metrics to {freport}.")

        # Plot the curve:
        pweight2main_metric = {
            pweight: pwegiht2metrics[pweight][args.report_metric]
            for pweight in passage_weights
        }
        fcurve_data = os.path.join(
            args.output_dir, f"passage_weight-vs-{args.report_metric}.json"
        )
        with open(fcurve_data, "w") as f:
            json.dump(pweight2main_metric, f, indent=4)
        logging.info(f"Saved the curve data to {fcurve_data}")
        main_metrics = [pweight2main_metric[pweight] for pweight in passage_weights]
        fcurve = os.path.join(
            args.output_dir, f"passage_weight-vs-{args.report_metric}.pdf"
        )
        plt.plot(passage_weights, main_metrics)
        plt.grid(linestyle="dashed")
        plt.xlabel("passage weight")
        plt.ylabel(f"{args.report_metric}")
        plt.savefig(fcurve, bbox_inches="tight")
