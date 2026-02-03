from abc import ABC, abstractmethod

class PredictionEngine(ABC):
    """
    Abstract Base Class for all Prediction Engines.
    Enforces a standard interface for predicting match outcomes.
    """

    @abstractmethod
    def predict_params(self, match_data: dict):
        """
        Returns (p_serve_p1, p_serve_p2) for the match.
        """
        pass

    def derive_markets(self, p1_serve_prob, p2_serve_prob, best_of=3):
        """
        Runs the standard Simulator to derive markets from service probabilities.
        This ensures all engines use the same math layer.
        """
        from .simulator import Simulator
        sim = Simulator(num_simulations=5000) # Standard count
        return sim.simulate_match(p1_serve_prob, p2_serve_prob, best_of=best_of)

    def predict_proba(self, match_data: dict) -> float:
        # Legacy compat - calculates via simulation
        p1, p2 = self.predict_params(match_data)
        markets = self.derive_markets(p1, p2)
        return markets['p_win']

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the engine (e.g., 'XGBoost v1', 'Heuristic v2')"""
        pass
