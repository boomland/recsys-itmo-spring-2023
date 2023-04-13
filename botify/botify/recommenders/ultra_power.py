from .random import Random
from .recommender import Recommender
import random
from typing import List
from .indexed import Indexed

class UltraPower(Recommender):

    def __init__(self,
                 tracks_redis,
                 recommendations_redis,
                 top_tracks,
                 catalog):
        
        self.tracks_redis = tracks_redis
        self.recommendations_redis = recommendations_redis
        self.catalog = catalog
        self.fallback = Indexed(tracks_redis,
                                recommendations_redis,
                                top_tracks,
                                catalog)
        self.random = Random(tracks_redis)
        
    def recommend_next(self,
                       user: int,
                       prev_track: int,
                       prev_track_time: float,
                       threshold: float = 0.8,
                       p_rand: float = 0.05) -> int:
        
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)
        
        play_random_track = (random.random() < p_rand)
        if play_random_track:
            return self.random.recommend_next(user, prev_track, prev_track_time)

        if (prev_track_time < threshold):
            return self.fallback.recommend_next(user, prev_track, prev_track_time)
        else:
            previous_track = self.catalog.from_bytes(previous_track)
            recommendations = previous_track.recommendations
            if not recommendations:
                return self.fallback.recommend_next(user, prev_track, prev_track_time)

            shuffled = list(recommendations)
            random.shuffle(shuffled)
            return shuffled[0]
