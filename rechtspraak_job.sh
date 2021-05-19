#!/bin/bash
#Set job requirements
#SBATCH --job-name="DECLUTR_pretrain"
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks-per-node=3
#SBATCH --time=1:00:00
#SBATCH --mem=2000M
#SBATCH --partition=gpu_shared
#SBATCH --gres=gpu:1

# Load modules, load conda, activate conda environment
module load 2020
module load Anaconda3
source activate declutr

# delete output folder from previous run
rm -rf output

#Run program
python3.7 allennlp/allennlp/__main__.py train "training_config/contrastive_only.jsonnet" \
 --serialization-dir "output" \
 --overrides "{'train_data_path': 'path/to/output/rechtspraak/train.txt'}" \
 --include-package "declutr"