"""
ML/DL Models Package
Advanced neural network models for learning disability prediction

Models:
- Dyslexia Neural Predictor v2.0
- Dyscalculia Neural Predictor v2.0
- Dysgraphia Neural Predictor v2.0

Unified API:
- UnifiedDisorderPredictor
- get_predictor()
"""

from ml_models.unified_predictor import (
    UnifiedDisorderPredictor,
    get_predictor
)

from ml_models.dyslexia_nn_model import DyslexiaDeepLearning
from ml_models.dyscalculia_nn_model import DyscalculiaDeepLearning
from ml_models.dysgraphia_nn_model import DysgraphiaDeepLearning

__version__ = "2.0"
__author__ = "NeroBoom ML Team"
__description__ = "Neural Network Models for Learning Disability Prediction"

__all__ = [
    'UnifiedDisorderPredictor',
    'get_predictor',
    'DyslexiaDeepLearning',
    'DyscalculiaDeepLearning',
    'DysgraphiaDeepLearning',
]

# Initialize global predictor on import
_predictor = get_predictor()

