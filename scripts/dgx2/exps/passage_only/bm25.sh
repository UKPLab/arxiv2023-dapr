datasets=( "ConditionalQA" "MSMARCO" "NaturalQuestions" "Genomics" "MIRACL" )
for dataset in ${datasets[@]}
do
    export DATA_DIR="data"
    export DATASET_PATH="$DATA_DIR/$dataset"
    export CLI_ARGS="
    --data_dir=$DATASET_PATH
    "
    export OUTPUT_DIR=$(python -m dapr.exps.passage_only.args.bm25 $CLI_ARGS)
    mkdir -p $OUTPUT_DIR
    export LOG_PATH="$OUTPUT_DIR/logging.log"
    echo "Logging file path: $LOG_PATH"
    python -m dapr.exps.passage_only.bm25 $CLI_ARGS > $LOG_PATH
done