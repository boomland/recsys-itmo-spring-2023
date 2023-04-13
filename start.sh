#!/bin/sh

cd botify/
docker-compose up -d --build
sleep 30
cd ../sim/
python sim/run.py --episodes 1000 --config config/env.yml single --recommender remote --seed 31337
rm ../logs/data.json
docker cp recommender-container:/app/log/data.json ../logs/data.json
cd ../botify
docker-compose stop
