"""Factory Boy model factories for test data generation."""

import factory
from factory.django import DjangoModelFactory

from levels.infrastructure.models import Level, Submit


class LevelFactory(DjangoModelFactory):
    """Generates Level test instances."""

    text = factory.Faker("paragraph")
    cost = factory.Faker("random_int", min=10, max=200)
    goal_wpm = factory.Faker("random_int", min=30, max=120)

    class Meta:
        model = Level


class SubmitFactory(DjangoModelFactory):
    """Generates Submit test instances."""

    level = factory.SubFactory(LevelFactory)
    user_id = factory.Faker("uuid4")
    wpm = factory.Faker("random_int", min=10, max=150)
    rewarded_credits = 0

    class Meta:
        model = Submit
