#/bin/sh
export LEADERBOARD_VERSION=v0.3.0
cd $1
curl -O https://storage.googleapis.com/crfm-helm-public/benchmark_output/archives/$LEADERBOARD_VERSION/run_stats.zip
mkdir -p ./benchmark_output/runs/$LEADERBOARD_VERSION
unzip run_stats.zip -d ./benchmark_output/runs/$LEADERBOARD_VERSION
rm run_stats.zip