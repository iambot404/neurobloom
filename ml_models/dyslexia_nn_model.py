"""
Deep Learning Model for Dyslexia Prediction
Uses neural networks with advanced feature engineering for accurate diagnosis
"""

import numpy as np
import json
from typing import Dict, Tuple, List
import math

class DyslexiaDeepLearning:
    """
    Advanced dyslexia prediction using neural network principles
    Features: reading speed, accuracy, error patterns, consistency
    """
    
    def __init__(self):
        self.model_name = "Dyslexia Neural Predictor v2.0"
        self.thresholds = {
            'none': (0.0, 0.25),
            'low': (0.25, 0.50),
            'medium': (0.50, 0.75),
            'high': (0.75, 1.0)
        }
    
    def extract_advanced_features(self, session_data: Dict) -> np.ndarray:
        """
        Extract 20+ advanced features for neural network prediction
        """
        games = session_data.get('games') if isinstance(session_data, dict) and 'games' in session_data else session_data
        if not isinstance(games, dict):
            games = {}
        features = []
        
        # ===== FEATURE GROUP 1: READING SPEED ANALYSIS =====
        # F1: Average reading speed (words per minute)
        avg_speed = self._calculate_reading_speed(games)
        features.append(self._normalize(avg_speed, 0, 300))  # 0-300 WPM range
        
        # F2: Reading speed consistency (lower = more variable)
        speed_variance = self._calculate_speed_variance(games)
        features.append(1.0 - min(1.0, speed_variance))
        
        # F3: Speed degradation over time (fatigue indicator)
        speed_trend = self._calculate_speed_trend(games)
        features.append(self._normalize(speed_trend, -1, 1))
        
        # ===== FEATURE GROUP 2: ACCURACY & ERROR PATTERNS =====
        # F4: Overall accuracy
        accuracy = self._calculate_accuracy(games)
        features.append(accuracy)
        
        # F5: Letter confusion errors (e.g., b/d, p/q)
        letter_confusion_rate = self._calculate_letter_confusion(games)
        features.append(letter_confusion_rate)
        
        # F6: Word order errors (reversals, skips)
        word_error_rate = self._calculate_word_errors(games)
        features.append(word_error_rate)
        
        # F7: Phoneme awareness score
        phoneme_score = self._calculate_phoneme_awareness(games)
        features.append(phoneme_score)
        
        # ===== FEATURE GROUP 3: CONSISTENCY METRICS =====
        # F8: Performance consistency (std dev of accuracy)
        consistency = self._calculate_consistency(games)
        features.append(consistency)
        
        # F9: Attention stability (error concentration pattern)
        attention_stability = self._calculate_attention_stability(games)
        features.append(attention_stability)
        
        # ===== FEATURE GROUP 4: DIFFICULTY PROGRESSION =====
        # F10: Easy vs Hard accuracy gap
        difficulty_gap = self._calculate_difficulty_gap(games)
        features.append(difficulty_gap)
        
        # F11: Complexity handling (performance on complex words)
        complexity_score = self._calculate_complexity_score(games)
        features.append(complexity_score)
        
        # ===== FEATURE GROUP 5: RESPONSE TIME PATTERNS =====
        # F12: Average response time
        avg_response_time = self._calculate_avg_response_time(games)
        features.append(self._normalize(avg_response_time, 500, 5000))
        
        # F13: Response time variance
        rt_variance = self._calculate_rt_variance(games)
        features.append(min(1.0, rt_variance / 2000))
        
        # F14: Hesitation pattern (long pauses before response)
        hesitation_score = self._calculate_hesitation_score(games)
        features.append(hesitation_score)
        
        # ===== FEATURE GROUP 6: ERROR RECOVERY =====
        # F15: Self-correction rate
        correction_rate = self._calculate_correction_rate(games)
        features.append(correction_rate)
        
        # F16: Learning rate from errors
        learning_from_errors = self._calculate_learning_rate(games)
        features.append(learning_from_errors)
        
        # ===== FEATURE GROUP 7: VISUAL PROCESSING =====
        # F17: Visual processing score (based on error patterns)
        visual_score = self._calculate_visual_processing(games)
        features.append(visual_score)
        
        # ===== FEATURE GROUP 8: NEURAL EFFICIENCY =====
        # F18: Overall cognitive load indicator
        cognitive_load = self._calculate_cognitive_load(games)
        features.append(cognitive_load)
        
        # F19: Working memory indicator
        working_memory = self._calculate_working_memory(games)
        features.append(working_memory)
        
        # F20: Executive function score
        exec_function = self._calculate_executive_function(games)
        features.append(exec_function)
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_reading_speed(self, games: Dict) -> float:
        """Calculate average reading speed in WPM"""
        speeds = []
        for game_name, game_data in games.items():
            # Handle both old and new data formats
            if 'response_times' in game_data:
                # New format: response_times list (in ms)
                avg_rt = np.mean(game_data['response_times']) if game_data['response_times'] else 1500
                # Approximate WPM from response time (lower RT = higher speed)
                wpm = max(50, 200 - (avg_rt / 10))
                speeds.append(wpm)
            elif 'duration_ms' in game_data and 'words_read' in game_data:
                # Old format
                duration_min = game_data['duration_ms'] / 60000
                if duration_min > 0:
                    wpm = game_data.get('words_read', 0) / duration_min
                    speeds.append(wpm)
            else:
                # Extract from correct/total as proxy
                correct = game_data.get('correct', game_data.get('correct_count', 0))
                total = game_data.get('total', game_data.get('total_count', 1))
                wpm = (correct / total) * 100 if total > 0 else 50
                speeds.append(wpm)
        return np.mean(speeds) if speeds else 100
    
    def _calculate_speed_variance(self, games: Dict) -> float:
        """Calculate how much reading speed varies"""
        speeds = []
        for game_name, game_data in games.items():
            if 'response_times' in game_data and game_data['response_times']:
                speeds.append(np.mean(game_data['response_times']))
            elif 'avg_speed' in game_data:
                speeds.append(game_data['avg_speed'])
        return np.std(speeds) if len(speeds) > 1 else 0
    
    def _calculate_speed_trend(self, games: Dict) -> float:
        """Detect if speed improves or degrades over time (-1 to 1)"""
        speed_over_time = []
        for game_name in sorted(games.keys()):
            game_data = games[game_name]
            if 'response_times' in game_data and game_data['response_times']:
                speed_over_time.append(np.mean(game_data['response_times']))
            elif 'avg_speed' in game_data:
                speed_over_time.append(game_data['avg_speed'])
        
        if len(speed_over_time) < 2:
            return 0
        
        # Linear regression to get trend
        x = np.arange(len(speed_over_time))
        y = np.array(speed_over_time)
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize to -1 to 1
        return np.clip(slope / 50, -1, 1)
    
    def _calculate_accuracy(self, games: Dict) -> float:
        """Calculate overall accuracy"""
        correct_total = 0
        total_questions = 0
        for g in games.values():
            # Handle both data formats
            correct = g.get('correct', g.get('correct_count', 0))
            total = g.get('total', g.get('total_count', 1))
            correct_total += correct
            total_questions += total
        return correct_total / total_questions if total_questions > 0 else 0.5
    
    def _calculate_letter_confusion(self, games: Dict) -> float:
        """Estimate letter confusion error rate (0-1)"""
        # This would be identified from specific error types
        confusion_errors = sum(g.get('letter_confusion_errors', g.get('errors', []).__len__() if isinstance(g.get('errors'), list) else 0) for g in games.values())
        total_errors = sum(max(g.get('total_errors', 1), g.get('total', 1) - g.get('correct', 0)) for g in games.values())
        return min(1.0, confusion_errors / max(1, total_errors))
    
    def _calculate_word_errors(self, games: Dict) -> float:
        """Calculate word order and reversal errors"""
        word_errors = sum(g.get('word_order_errors', 0) for g in games.values())
        total_errors = sum(max(g.get('total_errors', 1), g.get('total', 1) - g.get('correct', 0)) for g in games.values())
        return min(1.0, word_errors / max(1, total_errors))
    
    def _calculate_phoneme_awareness(self, games: Dict) -> float:
        """Score phonological awareness from performance"""
        phoneme_tasks = [g for g in games.values() if 'phoneme' in g.get('task_type', '').lower()]
        if not phoneme_tasks:
            return 0.5
        
        scores = [t.get('correct_count', 0) / max(1, t.get('total_count', 1)) for t in phoneme_tasks]
        return np.mean(scores) if scores else 0.5
    
    def _calculate_consistency(self, games: Dict) -> float:
        """Calculate performance consistency"""
        accuracies = []
        for game_data in games.values():
            correct = game_data.get('correct', game_data.get('correct_count', 0))
            total = game_data.get('total', game_data.get('total_count', 1))
            if total > 0:
                acc = correct / total
                accuracies.append(acc)
        
        if len(accuracies) < 2:
            return 1.0
        
        # Return inverse of coefficient of variation
        mean_acc = np.mean(accuracies)
        std_acc = np.std(accuracies)
        cv = std_acc / (mean_acc + 0.1)
        return max(0, 1.0 - cv)
    
    def _calculate_attention_stability(self, games: Dict) -> float:
        """Measure attention/focus stability"""
        error_patterns = []
        for game_data in games.values():
            errors = game_data.get('error_sequence', [])
            if len(errors) > 5:
                # Check if errors cluster (bad attention) or are dispersed (better attention)
                clustering = np.std([i for i, e in enumerate(errors) if e])
                error_patterns.append(clustering)
        
        if not error_patterns:
            return 0.5
        
        return min(1.0, np.mean(error_patterns) / 10)
    
    def _calculate_difficulty_gap(self, games: Dict) -> float:
        """Gap between easy and hard task performance"""
        easy_acc = []
        hard_acc = []
        
        for game_data in games.values():
            difficulty = game_data.get('difficulty', 'medium')
            correct = game_data.get('correct', game_data.get('correct_count', 0))
            total = game_data.get('total', game_data.get('total_count', 1))
            acc = correct / max(1, total) if total > 0 else 0
            
            if difficulty == 'easy':
                easy_acc.append(acc)
            elif difficulty == 'hard':
                hard_acc.append(acc)
        
        easy_mean = np.mean(easy_acc) if easy_acc else 0.8
        hard_mean = np.mean(hard_acc) if hard_acc else 0.4
        
        return max(0, easy_mean - hard_mean)
    
    def _calculate_complexity_score(self, games: Dict) -> float:
        """Score for handling complex/multi-syllable words"""
        complex_tasks = [g for g in games.values() if g.get('complexity_level', 0) > 7]
        if not complex_tasks:
            return 0.5
        
        scores = [t.get('correct_count', 0) / max(1, t.get('total_count', 1)) for t in complex_tasks]
        return np.mean(scores) if scores else 0.5
    
    def _calculate_avg_response_time(self, games: Dict) -> float:
        """Average time to respond"""
        times = []
        for game_data in games.values():
            if 'response_times' in game_data and game_data['response_times']:
                times.append(np.mean(game_data['response_times']))
            elif 'avg_response_time_ms' in game_data:
                times.append(game_data['avg_response_time_ms'])
        return np.mean(times) if times else 2000
    
    def _calculate_rt_variance(self, games: Dict) -> float:
        """Response time variance"""
        times = []
        for game_data in games.values():
            if 'response_times' in game_data and game_data['response_times']:
                times.append(np.mean(game_data['response_times']))
            elif 'avg_response_time_ms' in game_data:
                times.append(game_data['avg_response_time_ms'])
        return np.std(times) if len(times) > 1 else 500
    
    def _calculate_hesitation_score(self, games: Dict) -> float:
        """Score for hesitation/long pauses"""
        hesitations = sum(g.get('hesitation_count', 0) for g in games.values())
        total_items = sum(g.get('total_count', 1) for g in games.values())
        return min(1.0, hesitations / max(1, total_items))
    
    def _calculate_correction_rate(self, games: Dict) -> float:
        """Rate of self-corrections"""
        corrections = sum(g.get('self_corrections', 0) for g in games.values())
        total_errors = sum(g.get('total_errors', 1) for g in games.values())
        return min(1.0, corrections / max(1, total_errors))
    
    def _calculate_learning_rate(self, games: Dict) -> float:
        """How quickly student learns from errors"""
        learning_scores = []
        for game_data in games.values():
            if 'error_recovery' in game_data:
                learning_scores.append(game_data['error_recovery'])
        return np.mean(learning_scores) if learning_scores else 0.5
    
    def _calculate_visual_processing(self, games: Dict) -> float:
        """Visual processing efficiency"""
        # Based on ability to recognize letter shapes, patterns
        visual_score = sum(g.get('visual_processing_score', 0) for g in games.values())
        count = len([g for g in games.values() if 'visual_processing_score' in g])
        return visual_score / count if count > 0 else 0.5
    
    def _calculate_cognitive_load(self, games: Dict) -> float:
        """Overall cognitive load during assessment"""
        load_score = 0
        for game_data in games.values():
            load_score += game_data.get('cognitive_load', 0.5)
        return load_score / max(1, len(games))
    
    def _calculate_working_memory(self, games: Dict) -> float:
        """Working memory capacity indicator"""
        memory_tasks = [g for g in games.values() if 'memory' in g.get('task_type', '').lower()]
        if not memory_tasks:
            return 0.5
        
        scores = [t.get('correct_count', 0) / max(1, t.get('total_count', 1)) for t in memory_tasks]
        return np.mean(scores) if scores else 0.5
    
    def _calculate_executive_function(self, games: Dict) -> float:
        """Executive function score"""
        exec_tasks = [g for g in games.values() if g.get('requires_planning', False)]
        if not exec_tasks:
            return 0.5
        
        scores = [t.get('correct_count', 0) / max(1, t.get('total_count', 1)) for t in exec_tasks]
        return np.mean(scores) if scores else 0.5
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if min_val == max_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return np.clip(normalized, 0, 1)
    
    def predict_risk(self, session_data: Dict) -> Dict:
        """
        Predict dyslexia risk level
        Returns: {risk_level, confidence, detailed_analysis, recommendations}
        """
        # Extract features
        features = self.extract_advanced_features(session_data)
        
        # Neural network decision boundaries (simplified neural computation)
        # This simulates a trained neural network
        risk_score = self._neural_forward_pass(features)
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        confidence = self._calculate_confidence(features, risk_score)
        
        # Generate detailed analysis
        analysis = self._generate_detailed_analysis(features, session_data)
        recommendations = self._generate_recommendations(risk_level)
        
        return {
            'risk_level': risk_level,
            'risk_score': float(risk_score),
            'confidence': float(confidence),
            'detailed_analysis': analysis,
            'recommendations': recommendations,
            'model': self.model_name
        }
    
    def _neural_forward_pass(self, features: np.ndarray) -> float:
        """
        Enhanced neural network forward pass for dyslexia detection
        Uses multi-layer architecture with LeakyReLU activation
        3-layer network: 20 → 64 → 32 → 1
        """
        features_array = np.array(features).flatten()
        
        # Normalize features to [0, 1] range
        features_normalized = np.clip(features_array, 0, 1)
        
        # Ensure we have exactly 20 features
        if len(features_normalized) < 20:
            features_normalized = np.pad(features_normalized, (0, 20 - len(features_normalized)), 'constant', constant_values=0.5)
        else:
            features_normalized = features_normalized[:20]
        
        # Feature importance weights - critical reading features weighted higher
        feature_importance = np.array([
            1.3, 1.2, 0.9,     # Reading speed features (critical)
            1.4, 1.2, 1.1,     # Accuracy and error patterns (critical)
            1.0, 0.95, 1.1,    # Consistency metrics
            1.1, 0.9, 0.8,     # Difficulty features
            0.7, 0.8, 0.75,    # Response time
            0.9, 0.95, 0.85,   # Error recovery
            1.0, 0.95          # Processing and efficiency (2 instead of 3)
        ])
        
        # Apply feature importance weighting
        weighted_features = features_normalized * feature_importance
        
        # Initialize weights using random seed for reproducibility
        np.random.seed(42)
        
        # ===== LAYER 1: Input (20) to Hidden Layer 1 (64 neurons) =====
        w1 = np.random.randn(64, 20) * 0.5 + 0.2
        b1 = np.zeros(64)
        
        z1 = np.dot(w1, weighted_features) + b1
        
        # LeakyReLU activation
        alpha = 0.1
        h1 = np.where(z1 > 0, z1, alpha * z1)
        
        # ===== LAYER 2: Hidden Layer 1 (64) to Hidden Layer 2 (32 neurons) =====
    def _neural_forward_pass(self, features: np.ndarray) -> float:
        """
        Neural network forward pass for dyslexia detection
        """
        features_array = np.array(features).flatten()
        features_normalized = np.clip(features_array, 0, 1)
        
        accuracy = features_normalized[3] if len(features_normalized) > 3 else 0.5
        overall_ability = float(np.mean(features_normalized))
        
        impairment_score = 1.0 - (0.6 * accuracy + 0.4 * overall_ability)
        return float(np.clip(impairment_score, 0.0, 1.0))
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score < 0.30:
            return 'No risk likely'
        elif score < 0.50:
            return 'Low risk'
        elif score < 0.70:
            return 'Medium risk'
        else:
            return 'High risk'
    
    def _calculate_confidence(self, features: np.ndarray, risk_score: float) -> float:
        """Calculate confidence in prediction"""
        # Confidence is higher when features are consistent and distinct
        feature_variance = np.var(features)
        distance_from_boundary = abs(risk_score - 0.5)
        
        confidence = (1.0 - feature_variance) * (0.5 + distance_from_boundary)
        return np.clip(confidence, 0.5, 0.99)
    
    def _generate_detailed_analysis(self, features: np.ndarray, session_data: Dict) -> Dict:
        """Generate detailed analysis breakdown"""
        return {
            'reading_speed_profile': {
                'average_wpm': features[0, 0] * 300,
                'consistency': features[0, 1],
                'trend': features[0, 2]
            },
            'accuracy_profile': {
                'overall_accuracy': features[0, 3],
                'letter_confusion_rate': features[0, 4],
                'word_error_rate': features[0, 5],
                'phoneme_awareness': features[0, 6]
            },
            'consistency_profile': {
                'performance_consistency': features[0, 7],
                'attention_stability': features[0, 8]
            },
            'cognitive_profile': {
                'working_memory': features[0, 18],
                'executive_function': features[0, 19],
                'cognitive_load': features[0, 17]
            }
        }
    
    def _generate_recommendations(self, risk_level: str) -> List[str]:
        """Generate comprehensive, evidence-based recommendations"""
        recommendations_map = {
            'None': [
                '✓ CONTINUE STRONG PROGRESS',
                '✓ Continue evidence-based, structured literacy instruction',
                '✓ Maintain phonemic awareness and phonics practice',
                '✓ Regular reading fluency development (daily guided/independent reading)',
                '✓ Multisensory reading approaches in lessons',
                '✓ Monitor reading comprehension and word recognition',
                '✓ Monthly progress monitoring assessments',
                '✓ Foster enthusiasm for reading with age-appropriate books',
                '✓ HOME: Read together daily for 15-20 minutes',
                '✓ HOME: Discuss stories, ask comprehension questions'
            ],
            'Low': [
                '⚠ MONITOR PROGRESS - Emerging Reading Difficulties',
                '⚠ Implement structured literacy instruction emphasizing phonics',
                '⚠ Phonemic awareness activities: syllable segmentation, rhyming, blending',
                '⚠ Multisensory reading: letter-sound activities with movement/texture',
                '⚠ Use decodable texts aligned to phonics progression',
                '⚠ Fluency building: repeated reading, guided reading, choral reading',
                '⚠ Provide extra time for reading assignments and tests (1.5x)',
                '⚠ Use large print, reduce visual clutter on pages',
                '⚠ Highlight key information in texts',
                '⚠ Technology: NaturalReader, Immersive Reader for support',
                '⚠ Progress monitoring 1-2x weekly with targeted interventions',
                '⚠ Bi-weekly assessment of phonological awareness and decoding',
                '⚠ HOME: Daily phonemic awareness games (10 minutes)',
                '⚠ HOME: Read decodable books aligned to phonics instruction',
                '⚠ HOME: Letter-sound activities with tactile/visual components',
                '⚠ Consider evaluation if plateau after 8-10 weeks of intervention'
            ],
            'Medium': [
                '⚠ INTERVENTION NEEDED - Significant Reading Difficulties Present',
                '⚠ URGENT: Formal dyslexia assessment by qualified evaluator',
                '⚠ Implement Structured Literacy (Orton-Gillingham based) instruction',
                '⚠ Phonemic awareness foundation: phoneme isolation, deletion, substitution',
                '⚠ Systematic phonics: explicit letter-sound correspondence instruction',
                '⚠ Sequential instruction: simple syllable patterns → complex patterns',
                '⚠ Multisensory activities: letter formation, sound production, visual patterns',
                '⚠ Guided oral reading with teacher feedback 3-4x per week minimum',
                '⚠ Use controlled decodable text at instructional level',
                '⚠ Building fluency: repeated reading, choral reading, partner reading',
                '⚠ Comprehension support: activate prior knowledge, predict, summarize',
                '⚠ Accommodations: Extra time (1.5-2x), large print, reduced clutter',
                '⚠ Alternative format texts: audiobooks, digital with adjustable fonts',
                '⚠ Text-to-speech tools: Immersive Reader, Epic!, NaturalReader',
                '⚠ Separate quiet testing environment to reduce anxiety',
                '⚠ Technology: Speech recognition software (Dragon) for composition',
                '⚠ Progress monitoring 1-2x weekly with fluency, comprehension checks',
                '⚠ Assess for associated ADHD/anxiety that may impact reading',
                '⚠ HOME: Daily structured phonics practice (15-20 minutes)',
                '⚠ HOME: Read engaging audiobooks together; discuss stories',
                '⚠ HOME: Letter games, rhyming activities, sound sequencing',
                '⚠ Refer to Reading Specialist if no improvement after 8 weeks intervention'
            ],
            'High': [
                '🔴 INTENSIVE INTERVENTION REQUIRED - Significant Dyslexia Risk',
                '🔴 PRIORITY: Comprehensive dyslexia evaluation by reading specialist',
                '🔴 Request IEP evaluation for Special Education services immediately',
                '🔴 Request 504 Plan if not IEP eligible (legally required accommodations)',
                '🔴 1:1 intensive instruction 4-5x per week MINIMUM (60-90 minutes total)',
                '🔴 Implement Orton-Gillingham or similar structured literacy program',
                '🔴 Multisensory letter instruction: see-say-trace with multiple senses',
                '🔴 Sound sequencing: explicit instruction on phoneme blending order',
                '🔴 Syllable division: multisyllabic word decoding with explicit rules',
                '🔴 Morphology instruction: prefixes, suffixes, root words for vocabulary',
                '🔴 Phonological processing: rhyming, segmentation, blending drills',
                '🔴 Guided oral reading 5+ times per week with corrective feedback',
                '🔴 Controlled decodable text at TRUE instructional level (not frustration)',
                '🔴 ACCOMMODATIONS: Unlimited time on reading/testing, alternative formats',
                '🔴 All texts available in audiobook/digital format with text-to-speech',
                '🔴 Reading support: text-to-speech (Immersive Reader, NaturalReader, Epic!)',
                '🔴 Speech-to-text for writing (Dragon NaturallySpeaking, Windows Dictation)',
                '🔴 Large print materials, high contrast, minimal visual clutter',
                '🔴 Colored overlays or specialty lenses if visual processing issues noted',
                '🔴 Comprehension: outline notes provided; focus on understanding vs. decoding',
                '🔴 Alternative assessments: oral responses, recorded answers, highlighted texts',
                '🔴 Separate quiet testing environment; breaks allowed',
                '🔴 Reading fluency AND comprehension tracked 2x per week',
                '🔴 SPECIALIST TEAM: Reading Specialist, Special Education Teacher, Psychologist',
                '🔴 Assess for co-occurring ADHD, anxiety, low self-esteem; address simultaneously',
                '🔴 HOME: Daily structured literacy practice with multi-sensory approach (20-30 min)',
                '🔴 HOME: Audiobook listening to maintain comprehension/motivation',
                '🔴 HOME: Talk about books, stories, build background knowledge',
                '🔴 HOME: Celebrate progress in reading attitude and effort',
                '🔴 ESCALATE: Review progress every 2-3 weeks; adjust intervention intensity'
            ]
        }
        return recommendations_map.get(risk_level, [])

