export NCCL_DEBUG="INFO"
export CUDA_VISIBLE_DEVICES="2,9,10,11"

datasets=( "ConditionalQA" "MSMARCO" "NaturalQuestions" "Genomics" "MIRACL" )
for dataset in ${datasets[@]}
do
    export DATA_DIR="data"
    export DATASET_PATH="$DATA_DIR/$dataset"
    export CLI_ARGS="
    --data_dir=$DATASET_PATH
    "
    export OUTPUT_DIR=$(python -m dapr.exps.doc_retrieval_with_titles.args.spladev2 $CLI_ARGS)
    mkdir -p $OUTPUT_DIR
    export LOG_PATH="$OUTPUT_DIR/logging.log"
    echo "Logging file path: $LOG_PATH"
    # nohup torchrun --nproc_per_node=4 --master_port=29501 -m dapr.exps.doc_retrieval_with_titles.spladev2 $CLI_ARGS > $LOG_PATH &
    torchrun --nproc_per_node=4 --master_port=29503 -m dapr.exps.doc_retrieval_with_titles.spladev2 $CLI_ARGS > $LOG_PATH
done