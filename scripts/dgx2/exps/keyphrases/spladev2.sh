export NCCL_DEBUG="INFO"
export CUDA_VISIBLE_DEVICES="0,1,2,3"

datasets=( "ConditionalQA" "MSMARCO" "NaturalQuestions" "Genomics" "MIRACL" )
for dataset in ${datasets[@]}
do
    export DATA_DIR="data"
    export DATASET_PATH="$DATA_DIR/$dataset"
    export KEYPHRASES_PATH="$DATA_DIR/keyphrases/$dataset/did2dsum.jsonl"
    export CLI_ARGS="
    --data_dir=$DATASET_PATH
    --keyphrases_path=$KEYPHRASES_PATH
    "
    export OUTPUT_DIR=$(python -m dapr.exps.keyphrases.args.spladev2 $CLI_ARGS)
    mkdir -p $OUTPUT_DIR
    export LOG_PATH="$OUTPUT_DIR/logging.log"
    echo "Logging file path: $LOG_PATH"
    torchrun --nproc_per_node=4 --master_port=29501 -m dapr.exps.keyphrases.spladev2 $CLI_ARGS > $LOG_PATH
done