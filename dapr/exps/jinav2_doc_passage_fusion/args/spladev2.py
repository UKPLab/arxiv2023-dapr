from dataclasses import dataclass
import os
from clddp.utils import parse_cli
from dapr.exps.jinav2_doc_passage_fusion.args.base import (
    JinaV2DocPassageFusionArguments,
)


@dataclass
class SPLADEv2JinaV2DocPassageFusionArguments(JinaV2DocPassageFusionArguments):
    def build_output_dir(self) -> str:
        return os.path.join("exps/jinav2_doc_passage_fusion/spladev2", self.run_name)


if __name__ == "__main__":
    print(
        parse_cli(SPLADEv2JinaV2DocPassageFusionArguments).output_dir
    )  # For creating the logging path
