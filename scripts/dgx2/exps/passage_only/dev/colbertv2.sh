export NCCL_DEBUG="INFO"
export CUDA_VISIBLE_DEVICES="0,1,2,3"

export DATA_DIR="data"
export DATASET_PATH="$DATA_DIR/MSMARCO"
export CLI_ARGS="
--data_dir=$DATASET_PATH
--split=dev
"
export OUTPUT_DIR=$(python -m dapr.exps.passage_only.args.colbertv2 $CLI_ARGS)
mkdir -p $OUTPUT_DIR
export LOG_PATH="$OUTPUT_DIR/logging.log"
echo "Logging file path: $LOG_PATH"
setsid nohup torchrun --nproc_per_node=2 --master_port=29501 -m dapr.exps.passage_only.colbertv2 $CLI_ARGS > $LOG_PATH &