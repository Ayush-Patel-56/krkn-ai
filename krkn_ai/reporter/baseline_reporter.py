"""
Baseline Reporter for running and analyzing baseline scenarios.
"""

from typing import Optional

from krkn_ai.models.app import CommandRunResult
from krkn_ai.models.scenario.scenario_dummy import DummyScenario
from krkn_ai.models.config import ConfigFile
from krkn_ai.utils.logger import get_logger

logger = get_logger(__name__)


class BaselineReporter:
    """
    Reporter class for baseline scenario execution and regression analysis.

    This class handles the execution of baseline (dummy) scenarios and provides
    utilities for detecting regressions from the baseline fitness score.
    """

    def __init__(self, config: ConfigFile, krkn_client):
        """
        Initialize the baseline reporter.

        Args:
            config: Configuration used for this run.
            krkn_client: KrknRunner instance for executing scenarios.
        """
        self.config = config
        self.krkn_client = krkn_client
        self.baseline_result: Optional[CommandRunResult] = None

    def run_baseline(self, duration_seconds: int) -> CommandRunResult:
        """
        Run a baseline scenario (dummy scenario with no chaos).

        Args:
            duration_seconds: Duration to run the baseline scenario.

        Returns:
            CommandRunResult containing the baseline execution result.
        """
        dummy = DummyScenario(
            cluster_components=self.config.cluster_components
        )
        dummy.end.value = duration_seconds

        logger.info(
            "Running baseline (dummy scenario, %ds)",
            duration_seconds,
        )

        self.baseline_result = self.krkn_client.run(dummy, 0)

        logger.info(
            "Baseline fitness: %s",
            self.baseline_result.fitness_result.fitness_score,
        )

        return self.baseline_result

    def check_regression(
        self,
        scenario_result: CommandRunResult,
        threshold_percent: float
    ) -> bool:
        """
        Check if a scenario result represents a regression from the baseline.

        Args:
            scenario_result: The scenario result to check.
            threshold_percent: Percentage threshold for regression detection (0-100).
                              A value of 10.0 means 10% degradation is considered regression.

        Returns:
            True if the scenario is a regression from baseline, False otherwise.
        """
        if self.baseline_result is None:
            return False

        baseline_fitness = self.baseline_result.fitness_result.fitness_score
        scenario_fitness = scenario_result.fitness_result.fitness_score

        # Calculate the threshold as a percentage of baseline fitness
        threshold_value = baseline_fitness * (threshold_percent / 100.0)

        # Check if scenario fitness is worse than baseline by more than threshold
        is_regression = scenario_fitness < (baseline_fitness - threshold_value)

        if is_regression:
            degradation_percent = ((baseline_fitness - scenario_fitness) / baseline_fitness) * 100
            logger.info(
                "Regression from baseline detected (fitness %.4f < baseline %.4f, degradation: %.2f%%)",
                scenario_fitness,
                baseline_fitness,
                degradation_percent,
            )

        return is_regression

    def get_baseline_result(self) -> Optional[CommandRunResult]:
        """
        Get the baseline result if it has been run.

        Returns:
            The baseline CommandRunResult, or None if baseline hasn't been run.
        """
        return self.baseline_result
