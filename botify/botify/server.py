import json
import logging
import time
from dataclasses import asdict
from datetime import datetime

from flask import Flask
from flask_redis import Redis
from flask_restful import Resource, Api, abort, reqparse
from gevent.pywsgi import WSGIServer

from botify.data import DataLogger, Datum
from botify.experiment import Experiments, Treatment
from botify.recommenders.contextual import Contextual
from botify.recommenders.ultra_power import UltraPower
from botify.track import Catalog

import numpy as np

root = logging.getLogger()
root.setLevel("INFO")

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)
api = Api(app)

tracks_redis = Redis(app, config_prefix="REDIS_TRACKS")
tracks_redis_dnn_triplets = Redis(app, config_prefix="REDIS_TRACKS_DNN_TRIPLETS")
tracks_with_diverse_recs_redis = Redis(app, config_prefix="REDIS_TRACKS_WITH_DIVERSE_RECS")

artists_redis = Redis(app, config_prefix="REDIS_ARTIST")
recommendations_redis = Redis(app, config_prefix="REDIS_RECOMMENDATIONS")
recommendations_ub_redis = Redis(app, config_prefix="REDIS_RECOMMENDATIONS_UB")

data_logger = DataLogger(app)

catalog = Catalog(app).load(
    app.config["TRACKS_CATALOG"],
    app.config["TOP_TRACKS_CATALOG"]
)

catalog.upload_tracks(tracks_redis.connection)
catalog.upload_artists(artists_redis.connection)
catalog.upload_recommendations(recommendations_redis.connection,
                               "RECOMMENDATIONS_FILE_PATH")

catalog_ = Catalog(app).load(
    app.config["TRACKS_WITH_DNN_RECS_CATALOG"],
    app.config["TOP_TRACKS_CATALOG"]
)

catalog_.upload_tracks(tracks_redis.connection)
catalog_.upload_artists(artists_redis.connection)
catalog_.upload_recommendations(recommendations_redis.connection,
                                "RECOMMENDATIONS_FILE_PATH")


parser = reqparse.RequestParser()
parser.add_argument("track", type=int, location="json", required=True)
parser.add_argument("time", type=float, location="json", required=True)


class Hello(Resource):
    def get(self):
        return {
            "status": "alive",
            "message": "welcome to botify, the best toy music recommender",
        }

class Track(Resource):
    def get(self, track: int):
        data = tracks_redis.connection.get(track)
        if data is not None:
            return asdict(catalog.from_bytes(data))
        else:
            abort(404, description="Track not found")

class NextTrack(Resource):
    def post(self, user: int):
        start = time.time()

        args = parser.parse_args()

        treatment = Experiments.ULTRA_POWER.assign(user)
        if treatment == Treatment.T1:
            recommender = UltraPower(tracks_redis_dnn_triplets.connection,
                                     recommendations_redis.connection,
                                     catalog_.top_tracks[:100],
                                     catalog_)
        else:
            recommender = Contextual(tracks_redis.connection,
                                     catalog)

        recommendation = recommender.recommend_next(user,
                                                    args.track,
                                                    args.time)

        data_logger.log(
            "next",
            Datum(
                int(datetime.now().timestamp() * 1000),
                user,
                args.track,
                args.time,
                time.time() - start,
                recommendation,
            ),
        )
        return {"user": user, "track": recommendation}

class LastTrack(Resource):
    def post(self, user: int):
        start = time.time()
        args = parser.parse_args()
        data_logger.log(
            "last",
            Datum(
                int(datetime.now().timestamp() * 1000),
                user,
                args.track,
                args.time,
                time.time() - start,
            ),
        )
        return {"user": user}


api.add_resource(Hello, "/")
api.add_resource(Track, "/track/<int:track>")
api.add_resource(NextTrack, "/next/<int:user>")
api.add_resource(LastTrack, "/last/<int:user>")


if __name__ == "__main__":
    http_server = WSGIServer(("", 5000), app)
    http_server.serve_forever()