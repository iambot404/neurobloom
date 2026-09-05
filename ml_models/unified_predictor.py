"""
Unified ML/DL Model Integration
Manages all three neural network models for learning disability prediction
Provides unified API for assessment analysis
"""

import json
import numpy as np
from typing import Dict, Any
from ml_models.dyslexia_nn_model import DyslexiaDeepLearning
from ml_models.dyscalculia_nn_model import DyscalculiaDeepLearning
from ml_models.dysgraphia_nn_model import DysgraphiaDeepLearning


class UnifiedDisorderPredictor:
    """
    Unified interface for all three disorder prediction models
    Uses advanced neural networks for accurate diagnosis
    """
    
    def __init__(self):
        self.dyslexia_model = DyslexiaDeepLearning()
        self.dyscalculia_model = DyscalculiaDeepLearning()
        self.dysgraphia_model = DysgraphiaDeepLearning()
        
        self.model_version = "2.0 - Neural Networks"
        self.confidence_threshold = 0.65
    
    def predict_dyslexia(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict dyslexia risk using advanced neural network
        
        Args:
            session_data: Assessment session data including games/tasks
            
        Returns:
            Dictionary with risk_level, score, confidence, analysis, recommendations
        """
        try:
            prediction = self.dyslexia_model.predict_risk(session_data)
            prediction['assessment_type'] = 'dyslexia'
            prediction['timestamp'] = self._get_timestamp()
            return prediction
        except Exception as e:
            return self._error_response('dyslexia', str(e))
    
    def predict_dyscalculia(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict dyscalculia risk using advanced neural network
        
        Args:
            session_data: Assessment session data including games/tasks
            
        Returns:
            Dictionary with risk_level, score, confidence, analysis, recommendations
        """
        try:
            prediction = self.dyscalculia_model.predict_risk(session_data)
            prediction['assessment_type'] = 'dyscalculia'
            prediction['timestamp'] = self._get_timestamp()
            return prediction
        except Exception as e:
            return self._error_response('dyscalculia', str(e))
    
    def predict_dysgraphia(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict dysgraphia risk using advanced neural network
        
        Args:
            session_data: Assessment session data including games/tasks
            
        Returns:
            Dictionary with risk_level, score, confidence, analysis, recommendations
        """
        try:
            prediction = self.dysgraphia_model.predict_risk(session_data)
            prediction['assessment_type'] = 'dysgraphia'
            prediction['timestamp'] = self._get_timestamp()
            return prediction
        except Exception as e:
            return self._error_response('dysgraphia', str(e))
    
    def comprehensive_assessment(self, assessments: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Perform comprehensive assessment across all three disorders
        
        Args:
            assessments: Dictionary with keys 'dyslexia', 'dyscalculia', 'dysgraphia'
                        each containing session data
        
        Returns:
            Unified assessment report with all predictions and combined analysis
        """
        results = {}
        
        # Run all predictions
        if 'dyslexia' in assessments:
            results['dyslexia'] = self.predict_dyslexia(assessments['dyslexia'])
        
        if 'dyscalculia' in assessments:
            results['dyscalculia'] = self.predict_dyscalculia(assessments['dyscalculia'])
        
        if 'dysgraphia' in assessments:
            results['dysgraphia'] = self.predict_dysgraphia(assessments['dysgraphia'])
        
        # Generate comprehensive summary
        summary = self._generate_comprehensive_summary(results)
        
        return {
            'individual_results': results,
            'comprehensive_summary': summary,
            'model_version': self.model_version,
            'assessment_date': self._get_timestamp()
        }
    
    def _generate_comprehensive_summary(self, results: Dict) -> Dict[str, Any]:
        """Generate comprehensive assessment summary"""
        
        # Calculate overall risk profile
        risk_levels = [r.get('risk_level') for r in results.values()]
        risk_scores = [r.get('risk_score', 0) for r in results.values()]
        confidences = [r.get('confidence', 0.5) for r in results.values()]
        
        # Overall risk determination
        high_count = sum(1 for r in risk_levels if r == 'High')
        medium_count = sum(1 for r in risk_levels if r == 'Medium')
        
        if high_count >= 2:
            overall_risk = 'High'
        elif high_count == 1 or medium_count >= 2:
            overall_risk = 'Medium'
        elif medium_count == 1 or any(r == 'Low' for r in risk_levels):
            overall_risk = 'Low'
        else:
            overall_risk = 'None'
        
        # Average metrics
        avg_score = np.mean(risk_scores) if risk_scores else 0
        avg_confidence = np.mean(confidences) if confidences else 0
        
        # Generate combined recommendations
        combined_recommendations = self._combine_recommendations(results)
        
        # Risk profile
        risk_profile = {
            disorder: {
                'risk_level': results[disorder]['risk_level'],
                'risk_score': results[disorder]['risk_score'],
                'confidence': results[disorder]['confidence']
            }
            for disorder in results
        }
        
        summary = {
            'overall_risk_level': overall_risk,
            'average_risk_score': float(avg_score),
            'average_confidence': float(avg_confidence),
            'risk_profile': risk_profile,
            'combined_recommendations': combined_recommendations,
            'next_steps': self._generate_next_steps(overall_risk, results),
            'clinical_notes': self._generate_clinical_notes(results)
        }
        
        return summary
    
    def _combine_recommendations(self, results: Dict) -> list:
        """Combine recommendations from all three assessments"""
        all_recommendations = []
        
        for disorder, result in results.items():
            recommendations = result.get('recommendations', [])
            all_recommendations.extend(recommendations)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _generate_next_steps(self, overall_risk: str, results: Dict) -> list:
        """Generate recommended next steps based on assessment"""
        
        next_steps_map = {
            'High': [
                '1. Schedule comprehensive professional evaluation (Educational Psychologist)',
                '2. Request formal diagnosis from qualified specialist',
                '3. Develop Individualized Education Plan (IEP)',
                '4. Implement specialized intervention programs',
                '5. Request accommodations (extended time, assistive tech, etc.)',
                '6. Monitor progress with regular reassessment',
                '7. Coordinate with parents/guardians for home support'
            ],
            'Medium': [
                '1. Schedule follow-up assessment in 4-6 weeks',
                '2. Implement targeted intervention strategies',
                '3. Provide supplementary support materials',
                '4. Monitor progress closely',
                '5. Consider consultation with specialist if issues persist',
                '6. Provide recommended accommodations',
                '7. Regular progress monitoring'
            ],
            'Low': [
                '1. Continue current learning approach',
                '2. Regular monitoring and assessments',
                '3. Maintain current support level',
                '4. Provide enrichment activities',
                '5. Follow-up assessment in 6-12 months'
            ],
            'None': [
                '1. No immediate intervention needed',
                '2. Continue standard curriculum',
                '3. Annual screening recommended',
                '4. Encourage continued learning development'
            ]
        }
        
        return next_steps_map.get(overall_risk, [])
    
    def _generate_clinical_notes(self, results: Dict) -> str:
        """Generate detailed clinical notes"""
        
        notes = []
        
        for disorder, result in results.items():
            risk_level = result.get('risk_level', 'Unknown')
            confidence = result.get('confidence', 0)
            analysis = result.get('detailed_analysis', {})
            
            disorder_name = disorder.upper()
            notes.append(f"\n{disorder_name} ASSESSMENT:")
            notes.append(f"  Risk Level: {risk_level}")
            notes.append(f"  Confidence: {confidence:.1%}")
            
            # Add key findings from analysis
            for category, metrics in analysis.items():
                if isinstance(metrics, dict):
                    notable_items = [f"{k}: {v:.2f}" for k, v in metrics.items() if isinstance(v, (int, float))]
                    if notable_items:
                        notes.append(f"  {category.replace('_', ' ').title()}:")
                        for item in notable_items[:3]:  # Top 3 metrics
                            notes.append(f"    - {item}")
        
        return "\n".join(notes)
    
    def _error_response(self, disorder_type: str, error_message: str) -> Dict:
        """Generate error response"""
        return {
            'assessment_type': disorder_type,
            'risk_level': 'Unable to assess',
            'risk_score': 0,
            'confidence': 0,
            'error': error_message,
            'recommendations': ['Please ensure all assessment data is complete'],
            'model': self.model_version
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about models"""
        return {
            'version': self.model_version,
            'dyslexia_model': self.dyslexia_model.model_name,
            'dyscalculia_model': self.dyscalculia_model.model_name,
            'dysgraphia_model': self.dysgraphia_model.model_name,
            'features_per_model': 20,
            'activation_function': 'Sigmoid',
            'prediction_method': 'Neural Network with Feature Engineering',
            'confidence_threshold': self.confidence_threshold
        }


# Global predictor instance
_predictor = None

def get_predictor():
    """Get or create global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = UnifiedDisorderPredictor()
    return _predictor

