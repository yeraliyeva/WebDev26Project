from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serialises a single ranked leaderboard entry."""

    place = serializers.IntegerField()
    user_id = serializers.UUIDField()
    score = serializers.IntegerField()


class LeaderboardResponseSerializer(serializers.Serializer):
    """Serialises the full leaderboard response including the caller's rank."""

    top = LeaderboardEntrySerializer(many=True)
    user_place = serializers.IntegerField(allow_null=True)
    user_score = serializers.IntegerField()
