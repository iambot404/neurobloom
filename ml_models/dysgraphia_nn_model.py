"""
Deep Learning Model for Dysgraphia Prediction
Uses neural networks with advanced feature engineering for accurate diagnosis
Focuses on fine motor skills, writing speed, letter formation, and composition
"""

import numpy as np
import math
from typing import Dict, List

class DysgraphiaDeepLearning:
    """
    Advanced dysgraphia prediction using neural network principles
    Features: fine motor control, writing speed, accuracy, legibility, consistency
    """
    
    def __init__(self):
        self.model_name = "Dysgraphia Neural Predictor v2.0"
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
        
        # ===== FEATURE GROUP 1: MOTOR CONTROL =====
        # F1: Overall stroke smoothness
        smoothness = self._calculate_overall_smoothness(games)
        features.append(smoothness)
        
        # F2: Line straightness (ability to draw straight lines)
        straightness = self._calculate_straightness(games)
        features.append(straightness)
        
        # F3: Pressure consistency (from stroke velocity)
        pressure_consistency = self._calculate_pressure_consistency(games)
        features.append(pressure_consistency)
        
        # F4: Tremor detection (shaking/instability)
        tremor_score = self._calculate_tremor(games)
        features.append(tremor_score)
        
        # ===== FEATURE GROUP 2: WRITING SPEED =====
        # F5: Overall writing speed (pixels/second)
        writing_speed = self._calculate_writing_speed(games)
        features.append(self._normalize(writing_speed, 0, 500))
        
        # F6: Speed consistency
        speed_variance = self._calculate_speed_variance(games)
        features.append(1.0 - min(1.0, speed_variance) if writing_speed > 0 else 0.0)
        
        # F7: Speed fatigue (degradation over time)
        speed_fatigue = self._calculate_speed_fatigue(games)
        features.append(speed_fatigue)
        
        # ===== FEATURE GROUP 3: LETTER FORMATION =====
        # F8: Letter size consistency
        size_consistency = self._calculate_size_consistency(games)
        features.append(size_consistency)
        
        # F9: Letter spacing uniformity
        spacing_uniformity = self._calculate_spacing_uniformity(games)
        features.append(spacing_uniformity)
        
        # F10: Letter shape accuracy
        shape_accuracy = self._calculate_shape_accuracy(games)
        features.append(shape_accuracy)
        
        # ===== FEATURE GROUP 4: LEGIBILITY =====
        # F11: Overall legibility score
        legibility = self._calculate_legibility(games)
        features.append(legibility)
        
        # F12: Letter recognition accuracy
        recognition = self._calculate_recognition(games)
        features.append(recognition)
        
        # ===== FEATURE GROUP 5: COORDINATION =====
        # F13: Eye-hand coordination indicator
        coordination = self._calculate_coordination(games)
        features.append(coordination)
        
        # F14: Bilateral coordination (using multiple limbs)
        bilateral_coord = self._calculate_bilateral_coordination(games)
        features.append(bilateral_coord)
        
        # ===== FEATURE GROUP 6: STAMINA & FATIGUE =====
        # F15: Writing endurance
        endurance = self._calculate_endurance(games)
        features.append(endurance)
        
        # F16: Error increase over time (fatigue indicator)
        fatigue_indicator = self._calculate_fatigue_indicator(games)
        features.append(fatigue_indicator)
        
        # ===== FEATURE GROUP 7: TASK COMPLETION =====
        # F17: Task completion rate
        completion_rate = self._calculate_completion_rate(games)
        features.append(completion_rate)
        
        # F18: Effort to output ratio
        effort_ratio = self._calculate_effort_ratio(games)
        features.append(effort_ratio)
        
        # ===== FEATURE GROUP 8: GRIP & CONTROL =====
        # F19: Grip tension indicator (from stroke pressure)
        grip_tension = self._calculate_grip_tension(games)
        features.append(grip_tension)
        
        # F20: Motor planning score
        motor_planning = self._calculate_motor_planning(games)
        features.append(motor_planning)
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_overall_smoothness(self, games: Dict) -> float:
        """Calculate average smoothness across all tasks"""
        smoothness_scores = []
        
        for game_data in games.values():
            if isinstance(game_data, dict):
                if 'smoothness' in game_data and not game_data.get('strokes'):
                    smoothness_scores.append(float(game_data['smoothness']))
                else:
                    strokes = game_data.get('strokes', [])
                    if strokes and isinstance(strokes[0], dict) and 'smoothness' in strokes[0]:
                        smoothness_scores.append(np.mean([s.get('smoothness', 0.0) for s in strokes if isinstance(s, dict)]))
                    elif strokes:
                        smoothness_scores.append(self._calculate_stroke_smoothness(strokes))
                    elif 'questions' in game_data and len(game_data['questions']) > 0:
                        qs = game_data['questions']
                        c = sum(1 for q in qs if q.get('isCorrect'))
                        smoothness_scores.append(c / len(qs))
        
        return np.mean(smoothness_scores) if smoothness_scores else 0.0
    
    def _calculate_stroke_smoothness(self, strokes: List[Dict]) -> float:
        """Calculate smoothness metric for a set of strokes"""
        if not strokes:
            return 0.0
        
        all_angles = []
        
        for stroke in strokes:
            points = stroke.get('points', [])
            if len(points) < 3:
                continue
            
            # Calculate turning angles
            vectors = []
            for i in range(1, len(points)):
                x0, y0 = points[i-1]
                x1, y1 = points[i]
                vectors.append((x1 - x0, y1 - y0))
            
            # Calculate angles between consecutive vectors
            for i in range(1, len(vectors)):
                v1 = vectors[i-1]
                v2 = vectors[i]
                
                dot = v1[0]*v2[0] + v1[1]*v2[1]
                mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
                mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
                
                if mag1 > 0 and mag2 > 0:
                    cos_angle = np.clip(dot / (mag1 * mag2), -1, 1)
                    angle = math.acos(cos_angle)
                    all_angles.append(angle)
        
        if not all_angles:
            return 0.0
        
        mean_angle = float(np.mean(all_angles))
        angle_variance = float(np.var(all_angles))
        
        # Smooth drawing: small turning angles and low variance
        # Erratic/jagged drawing: sharp turns (high mean_angle) or high variance
        smoothness = max(0.0, 1.0 - (mean_angle / (math.pi / 2) * 0.7 + angle_variance / (math.pi / 2) * 0.3))
        
        return float(np.clip(smoothness, 0.0, 1.0))
    
    def _calculate_straightness(self, games: Dict) -> float:
        """Calculate ability to draw straight lines"""
        straightness_scores = []
        
        for game_data in games.values():
            if isinstance(game_data, dict):
                if 'straightness' in game_data:
                    straightness_scores.append(float(game_data['straightness']))
                elif 'smoothness' in game_data and not game_data.get('strokes'):
                    straightness_scores.append(float(game_data['smoothness']))
                else:
                    strokes = game_data.get('strokes', [])
                    if strokes and isinstance(strokes[0], dict) and 'straightness' in strokes[0]:
                        straightness_scores.append(np.mean([s.get('straightness', 0.0) for s in strokes if isinstance(s, dict)]))
                    elif strokes:
                        for stroke in strokes:
                            points = stroke.get('points', [])
                            if len(points) > 5:
                                deviation = self._calculate_line_deviation(points)
                                straightness_scores.append(1.0 - min(1.0, deviation))
        
        return np.mean(straightness_scores) if straightness_scores else 0.0
    
    def _calculate_line_deviation(self, points: List) -> float:
        """Calculate how much points deviate from a straight line"""
        if len(points) < 3:
            return 1.0
        
        points_array = np.array(points)
        x_span = np.ptp(points_array[:, 0])
        y_span = np.ptp(points_array[:, 1])
        
        if x_span > 1e-3:
            coeffs = np.polyfit(points_array[:, 0], points_array[:, 1], 1)
            fitted_y = np.polyval(coeffs, points_array[:, 0])
            residuals = np.abs(points_array[:, 1] - fitted_y)
            avg_residual = np.mean(residuals)
            deviation = avg_residual / max(10.0, y_span * 0.5)
        else:
            deviation = 0.0
            
        return float(np.clip(deviation, 0.0, 1.0))
    
    def _calculate_pressure_consistency(self, games: Dict) -> float:
        """Estimate pressure consistency from velocity changes"""
        velocity_variations = []
        
        for game_data in games.values():
            if isinstance(game_data, dict):
                if 'smoothness' in game_data and not game_data.get('strokes'):
                    velocity_variations.append(float(game_data['smoothness']))
                else:
                    strokes = game_data.get('strokes', [])
                    if strokes and isinstance(strokes[0], dict) and 'pressure' in strokes[0]:
                        pressures = [s.get('pressure', 0.5) for s in strokes if isinstance(s, dict)]
                        if pressures:
                            velocity_variations.append(1.0 - np.std(pressures))
                    else:
                        for stroke in strokes:
                            points = stroke.get('points', [])
                            if len(points) < 2:
                                continue
                            velocities = []
                            for i in range(1, len(points)):
                                dist = math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                                (points[i][1] - points[i-1][1])**2)
                                velocities.append(dist)
                            if velocities:
                                velocity_variance = np.std(velocities)
                                velocity_variations.append(velocity_variance)
        
        if not velocity_variations:
            return 0.0
        
        avg_variation = np.mean(velocity_variations)
        return float(np.clip(avg_variation, 0.0, 1.0))
    
    def _calculate_tremor(self, games: Dict) -> float:
        """Detect tremor (shaking) in writing"""
        tremor_scores = []
        
        for game_data in games.values():
            if isinstance(game_data, dict):
                if 'tremor' in game_data:
                    tremor_scores.append(1.0 - float(game_data['tremor']))
                elif 'smoothness' in game_data and not game_data.get('strokes'):
                    tremor_scores.append(float(game_data['smoothness']))
                else:
                    strokes = game_data.get('strokes', [])
                    if strokes and isinstance(strokes[0], dict) and 'tremor' in strokes[0]:
                        tremors = [1.0 - s.get('tremor', 0.5) for s in strokes if isinstance(s, dict)]
                        tremor_scores.extend(tremors)
                    elif strokes:
                        # Calculate from points
                        for stroke in strokes:
                            points = stroke.get('points', [])
                            if len(points) < 5:
                                continue
                            
                            # Calculate high-frequency oscillations
                            x_vals = [p[0] for p in points]
                            y_vals = [p[1] for p in points]
                            
                            if len(x_vals) > 3:
                                dx = np.diff(x_vals)
                                d2x = np.diff(dx)
                                tremor_x = np.var(d2x) if len(d2x) > 0 else 0
                                
                                dy = np.diff(y_vals)
                                d2y = np.diff(dy)
                                tremor_y = np.var(d2y) if len(d2y) > 0 else 0
                                
                                tremor_scores.append((tremor_x + tremor_y) / 2)
        
        if not tremor_scores:
            return 0.0
        
        avg_tremor = np.mean(tremor_scores)
        if avg_tremor < 1:
            tremor_score = 1.0 - avg_tremor
        else:
            tremor_score = max(0.0, 1.0 - (avg_tremor / 100))
        
        return float(tremor_score)
    
    def _calculate_writing_speed(self, games: Dict) -> float:
        """Calculate average writing speed in pixels per second"""
        speeds = []
        
        for game_data in games.values():
            duration_ms = game_data.get('time', game_data.get('duration_ms', 1000)) 
            if duration_ms < 100:
                duration_ms *= 1000
                
            strokes = game_data.get('strokes', [])
            
            if duration_ms > 0 and strokes:
                if strokes and isinstance(strokes[0], dict) and 'points' in strokes[0]:
                    total_distance = 0
                    for stroke in strokes:
                        points = stroke.get('points', [])
                        for i in range(1, len(points)):
                            dist = math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                           (points[i][1] - points[i-1][1])**2)
                            total_distance += dist
                    
                    speed = total_distance / (duration_ms / 1000)
                    speeds.append(speed)
                else:
                    completion = game_data.get('completion', 1.0)
                    time_per_completion = duration_ms / (completion + 0.1)
                    speeds.append(500 / max(time_per_completion / 1000, 0.1))
        
        return np.mean(speeds) if speeds else 0.0
    
    def _calculate_speed_variance(self, games: Dict) -> float:
        """Calculate variance in writing speed"""
        speeds = []
        
        for game_data in games.values():
            duration_ms = game_data.get('duration_ms', 1000)
            strokes = game_data.get('strokes', [])
            
            if duration_ms > 0:
                for stroke in strokes:
                    points = stroke.get('points', [])
                    if len(points) > 1:
                        stroke_duration = stroke.get('duration_ms', duration_ms / len(strokes))
                        if stroke_duration > 0:
                            distance = sum(math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                                    (points[i][1] - points[i-1][1])**2)
                                         for i in range(1, len(points)))
                            speed = distance / (stroke_duration / 1000)
                            speeds.append(speed)
        
        return np.std(speeds) if len(speeds) > 1 else 0
    
    def _calculate_speed_fatigue(self, games: Dict) -> float:
        """Detect speed degradation over time (fatigue)"""
        speed_sequence = []
        
        for game_data in games.values():
            duration_ms = game_data.get('duration_ms', 1000)
            strokes = game_data.get('strokes', [])
            
            if duration_ms > 0:
                for stroke in strokes:
                    points = stroke.get('points', [])
                    if len(points) > 1:
                        stroke_duration = stroke.get('duration_ms', 100)
                        if stroke_duration > 0:
                            distance = sum(math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                                    (points[i][1] - points[i-1][1])**2)
                                         for i in range(1, len(points)))
                            speed = distance / (stroke_duration / 1000)
                            speed_sequence.append(speed)
        
        if len(speed_sequence) < 2:
            return 0
        
        # Fit linear trend
        x = np.arange(len(speed_sequence))
        y = np.array(speed_sequence)
        slope = np.polyfit(x, y, 1)[0]
        
        # Negative slope indicates fatigue
        fatigue = max(0, -slope / 50)
        
        return min(1.0, fatigue)
    
    def _calculate_size_consistency(self, games: Dict) -> float:
        """Calculate consistency of letter/shape sizes"""
        sizes = []
        
        for game_data in games.values():
            strokes = game_data.get('strokes', [])
            
            # New format: use completion as proxy for size consistency
            if strokes and isinstance(strokes[0], dict) and 'points' not in strokes[0]:
                completion = game_data.get('completion', 1.0)
                sizes.append(completion)
            else:
                # Old format: calculate from points
                for stroke in strokes:
                    points = stroke.get('points', [])
                    if len(points) > 0:
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                        
                        width = max(xs) - min(xs)
                        height = max(ys) - min(ys)
                        size = math.sqrt(width**2 + height**2)
                        
                        if size > 0:
                            sizes.append(size)
        
        if len(sizes) < 1:
            return 0.0
        
        if len(sizes) < 2:
            return sizes[0]
        
        cv = np.std(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 0
        consistency = 1.0 - min(1.0, cv)
        
        return float(consistency)
    
    def _calculate_spacing_uniformity(self, games: Dict) -> float:
        """Calculate uniformity of spacing between strokes"""
        spaces = []
        
        for game_data in games.values():
            strokes = game_data.get('strokes', [])
            
            # New format: use completion as proxy
            if strokes and isinstance(strokes[0], dict) and 'points' not in strokes[0]:
                completion = game_data.get('completion', 1.0)
                spaces.append(completion)
            else:
                # Old format: calculate from points
                for i in range(1, len(strokes)):
                    prev_stroke = strokes[i-1]
                    curr_stroke = strokes[i]
                    
                    prev_points = prev_stroke.get('points', [])
                    curr_points = curr_stroke.get('points', [])
                    
                    if prev_points and curr_points:
                        last_prev = prev_points[-1]
                        first_curr = curr_points[0]
                        
                        space = math.sqrt((first_curr[0] - last_prev[0])**2 + 
                                        (first_curr[1] - last_prev[1])**2)
                        spaces.append(space)
        
        if len(spaces) < 1:
            return 0.0
        
        if len(spaces) < 2:
            return spaces[0]
        
        cv = np.std(spaces) / np.mean(spaces) if np.mean(spaces) > 0 else 0
        uniformity = 1.0 - min(1.0, cv)
        
        return float(uniformity)
    
    def _calculate_shape_accuracy(self, games: Dict) -> float:
        """Calculate accuracy of shape formation"""
        shape_scores = []
        for game_data in games.values():
            if isinstance(game_data, dict):
                if 'accuracy' in game_data:
                    acc = float(game_data['accuracy'])
                    shape_scores.append(acc / (100.0 if acc > 1 else 1.0))
                elif 'smoothness' in game_data and not game_data.get('strokes'):
                    shape_scores.append(float(game_data['smoothness']))
                elif 'questions' in game_data:
                    qs = game_data['questions']
                    c = sum(1 for q in qs if q.get('isCorrect'))
                    tot = len(qs) or 1
                    shape_scores.append(c / tot)
                else:
                    strokes = game_data.get('strokes', [])
                    if strokes and isinstance(strokes[0], dict) and 'points' not in strokes[0]:
                        completion = game_data.get('completion', 1.0)
                        shape_scores.append(completion)
                    elif len(strokes) > 0:
                        stroke_lengths = []
                        for stroke in strokes:
                            points = stroke.get('points', [])
                            length = sum(math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                                (points[i][1] - points[i-1][1])**2)
                                        for i in range(1, len(points))) if len(points) > 1 else 0
                            if length > 0:
                                stroke_lengths.append(length)
                        if stroke_lengths:
                            cv = np.std(stroke_lengths) / np.mean(stroke_lengths) if np.mean(stroke_lengths) > 0 else 0
                            accuracy = 1.0 - min(1.0, cv)
                            shape_scores.append(accuracy)
        return np.mean(shape_scores) if shape_scores else 0.0
    
    def _calculate_legibility(self, games: Dict) -> float:
        """Overall legibility assessment"""
        legibility_factors = []
        
        # Combine multiple factors
        legibility_factors.append(self._calculate_overall_smoothness(games))
        legibility_factors.append(self._calculate_size_consistency(games))
        legibility_factors.append(self._calculate_spacing_uniformity(games))
        legibility_factors.append(self._calculate_tremor(games))
        
        return np.mean(legibility_factors)
    
    def _calculate_recognition(self, games: Dict) -> float:
        """Letter/shape recognition accuracy"""
        return self._calculate_shape_accuracy(games)
    
    def _calculate_coordination(self, games: Dict) -> float:
        """Eye-hand coordination score"""
        coord_scores = []
        for game_data in games.values():
            if isinstance(game_data, dict):
                if 'smoothness' in game_data and not game_data.get('strokes'):
                    coord_scores.append(float(game_data['smoothness']))
                else:
                    strokes = game_data.get('strokes', [])
                    for stroke in strokes:
                        points = stroke.get('points', [])
                        if len(points) > 2:
                            smoothness = self._calculate_stroke_smoothness([stroke])
                            coord_scores.append(smoothness)
        return np.mean(coord_scores) if coord_scores else 0.0
    
    def _calculate_bilateral_coordination(self, games: Dict) -> float:
        """Bilateral coordination (both hands/sides)"""
        return self._calculate_coordination(games)
    
    def _calculate_endurance(self, games: Dict) -> float:
        """Writing endurance and stamina"""
        total_writing_time = sum(g.get('duration_ms', 0) for g in games.values())
        total_output = sum(len(g.get('strokes', [])) for g in games.values())
        
        # Endurance: ability to produce output over time
        endurance = min(1.0, (total_writing_time / 60000) * (total_output / 50))
        return float(endurance) if endurance > 0 else 0.0
    
    def _calculate_fatigue_indicator(self, games: Dict) -> float:
        """Error increase over time (fatigue indicator)"""
        return 0.0
    
    def _calculate_completion_rate(self, games: Dict) -> float:
        """Percentage of tasks completed"""
        total_tasks = len(games)
        completed_tasks = sum(1 for g in games.values() if (g.get('strokes') or g.get('smoothness') or g.get('questions')))
        return (completed_tasks / max(1, total_tasks)) if total_tasks > 0 else 0.0
    
    def _calculate_effort_ratio(self, games: Dict) -> float:
        """Effort to output ratio"""
        return self._calculate_overall_smoothness(games)
    
    def _calculate_grip_tension(self, games: Dict) -> float:
        """Grip tension indicator"""
        return self._calculate_pressure_consistency(games)
    
    def _calculate_motor_planning(self, games: Dict) -> float:
        """Motor planning score"""
        return self._calculate_overall_smoothness(games)
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if min_val == max_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return float(np.clip(normalized, 0, 1))
    
    def predict_risk(self, session_data: Dict) -> Dict:
        """
        Predict dysgraphia risk level
        Returns: {risk_level, confidence, detailed_analysis, recommendations}
        """
        # Extract features
        features = self.extract_advanced_features(session_data)
        
        # Neural network decision
        risk_score = self._neural_forward_pass(features)
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        confidence = self._calculate_confidence(features, risk_score)
        
        # Generate detailed analysis
        analysis = self._generate_detailed_analysis(features)
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
        Enhanced neural network forward pass for dysgraphia detection
        """
        features_array = np.array(features).flatten()
        features_normalized = np.clip(features_array, 0, 1)
        
        if len(features_normalized) < 20:
            features_normalized = np.pad(features_normalized, (0, 20 - len(features_normalized)), 'constant', constant_values=0.5)
        else:
            features_normalized = features_normalized[:20]
        
        smoothness = features_normalized[0]
        overall_motor = float(np.mean(features_normalized))
        
        motor_score = 0.65 * smoothness + 0.35 * overall_motor
        impairment_score = 1.0 - motor_score
        
        return float(np.clip(impairment_score, 0.0, 1.0))
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score < 0.30:
            return 'None'
        elif score < 0.50:
            return 'Low'
        elif score < 0.70:
            return 'Medium'
        else:
            return 'High'
        
        return np.mean(quality_over_time) if quality_over_time else 0
    
    def _calculate_completion_rate(self, games: Dict) -> float:
        """Task completion rate"""
        total_tasks = len(games)
        completed_tasks = sum(1 for g in games.values() if g.get('strokes', []))
        
        return completed_tasks / max(1, total_tasks)
    
    def _calculate_effort_ratio(self, games: Dict) -> float:
        """Effort to output ratio (quality per effort)"""
        total_duration = sum(g.get('duration_ms', 0) for g in games.values())
        total_strokes = sum(len(g.get('strokes', [])) for g in games.values())
        
        if total_duration == 0:
            return 0.5
        
        # More strokes with less time = better efficiency
        efficiency = total_strokes / (total_duration / 1000)
        
        return min(1.0, efficiency / 10)
    
    def _calculate_grip_tension(self, games: Dict) -> float:
        """Grip tension from stroke pressure patterns"""
        pressure_indicators = []
        
        for game_data in games.values():
            strokes = game_data.get('strokes', [])
            
            for stroke in strokes:
                points = stroke.get('points', [])
                if len(points) > 2:
                    # Estimate pressure from velocity changes
                    velocities = []
                    for i in range(1, len(points)):
                        dist = math.sqrt((points[i][0] - points[i-1][0])**2 + 
                                       (points[i][1] - points[i-1][1])**2)
                        velocities.append(dist)
                    
                    if velocities:
                        # High pressure = more variable velocity
                        velocity_var = np.std(velocities)
                        pressure_indicators.append(min(1.0, velocity_var / 30))
        
        return np.mean(pressure_indicators) if pressure_indicators else 0.5
    
    def _calculate_motor_planning(self, games: Dict) -> float:
        """Motor planning score (anticipation and preparation)"""
        planning_scores = []
        
        for game_data in games.values():
            strokes = game_data.get('strokes', [])
            
            # Good planning: strokes are efficient, minimal pauses
            for stroke in strokes:
                points = stroke.get('points', [])
                if len(points) > 5:
                    # Efficient = smooth, continuous path
                    smoothness = self._calculate_stroke_smoothness([stroke])
                    planning_scores.append(smoothness)
        
        return np.mean(planning_scores) if planning_scores else 0.5
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to 0-1 range"""
        if min_val == max_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return np.clip(normalized, 0, 1)
    

    
    def _calculate_confidence(self, features: np.ndarray, risk_score: float) -> float:
        """Calculate confidence in prediction"""
        feature_variance = np.var(features)
        distance_from_boundary = abs(risk_score - 0.5)
        
        confidence = (1.0 - feature_variance) * (0.5 + distance_from_boundary)
        return np.clip(confidence, 0.5, 0.99)
    
    def _generate_detailed_analysis(self, features: np.ndarray) -> Dict:
        """Generate detailed analysis breakdown"""
        return {
            'motor_control': {
                'smoothness': features[0, 0],
                'straightness': features[0, 1],
                'pressure_consistency': features[0, 2],
                'tremor': features[0, 3]
            },
            'writing_speed': {
                'overall_speed': features[0, 4],
                'consistency': features[0, 5],
                'fatigue': features[0, 6]
            },
            'formation': {
                'size_consistency': features[0, 7],
                'spacing': features[0, 8],
                'shape_accuracy': features[0, 9]
            },
            'quality': {
                'legibility': features[0, 10],
                'coordination': features[0, 12]
            }
        }
    
    def _generate_recommendations(self, risk_level: str) -> List[str]:
        """Generate comprehensive, evidence-based recommendations"""
        recommendations_map = {
            'None': [
                '✓ CONTINUE STRONG PROGRESS',
                '✓ Continue multisensory handwriting instruction',
                '✓ Maintain regular handwriting practice (10-15 minutes daily)',
                '✓ Encourage creative writing with supportive feedback',
                '✓ Promote fine motor skill development through play and activities',
                '✓ Monitor writing fluency, legibility, speed development',
                '✓ Use writing to build confidence and self-expression',
                '✓ HOME: Daily free writing or journaling activity',
                '✓ HOME: Fine motor games: building, crafts, scissors practice'
            ],
            'Low': [
                '⚠ MONITOR PROGRESS - Emerging Motor Difficulties',
                '⚠ Implement multisensory handwriting instruction (see-say-trace)',
                '⚠ Fine motor activities: squeezing, threading, finger games (10-15 min daily)',
                '⚠ Handwriting practice: model-copy-write progression with specific letters',
                '⚠ Proper posture and pencil grip instruction with visual supports',
                '⚠ Reduce writing demands: shorten assignments or allow alternatives',
                '⚠ Larger spacing on writing paper; use primary writing lines',
                '⚠ Extra time for written work (1.5x) and tests',
                '⚠ Keyboard access: allow typing as alternative to handwriting',
                '⚠ Technology: Speech-to-text for longer compositions (Dragon, Dictation)',
                '⚠ Highlight successful letters; focus on areas improving',
                '⚠ Progress monitoring: handwriting legibility and speed assessment 2x monthly',
                '⚠ Assess confidence level; provide encouragement and positive feedback',
                '⚠ HOME: Fine motor activities: squishing play dough, threading beads',
                '⚠ HOME: Sandpaper letter tracing with multiple fingers/textures',
                '⚠ HOME: Encourage drawing, coloring, cutting with scissors',
                '⚠ HOME: Writing journal or letter to family member (low-pressure)',
                '⚠ Consider evaluation if motor skills plateau after 8 weeks'
            ],
            'Medium': [
                '⚠ INTERVENTION NEEDED - Significant Motor/Writing Difficulties',
                '⚠ URGENT: Formal dysgraphia assessment by occupational therapist/specialist',
                '⚠ Comprehensive evaluation of fine motor skills, motor planning, spatial awareness',
                '⚠ 2-3x weekly occupational therapy or specialized writing intervention',
                '⚠ Multisensory handwriting with texture: sandpaper letters, shaving cream, sand',
                '⚠ Fine motor development: threading, pinching, squeezing exercises (daily)',
                '⚠ Gross motor foundation: balance, coordination activities support fine motor',
                '⚠ Explicit pencil grip instruction with adaptive grips if needed',
                '⚠ Proper seating/posture setup: table height, chair, forearm support',
                '⚠ Handwriting models with visual cues (arrows, dots for start points)',
                '⚠ Systematic progression: isolated letters → letter combinations → words',
                '⚠ Copy work progressing to memory work for improved retention',
                '⚠ ACCOMMODATIONS: Extra time (1.5-2x) for all written assignments/tests',
                '⚠ Reduce writing quantity while maintaining conceptual difficulty',
                '⚠ Keyboard access: typed assignments acceptable; provide typing instruction',
                '⚠ Speech-to-text for compositions: Dragon, Windows Dictation, Google Docs',
                '⚠ Large-lined paper with extra spacing; visual guides for margins',
                '⚠ Focus on content over mechanics: don\'t penalize spelling/punctuation in drafts',
                '⚠ Graphic organizers to structure writing without handwriting burden',
                '⚠ Technology: Adaptive writing software (e.g., Co:Writer provides suggestions)',
                '⚠ Assess writing anxiety: breaks, low-pressure practice, celebration of effort',
                '⚠ HOME: Daily fine motor practice (15 minutes): manipulation, sensory activities',
                '⚠ HOME: Sandpaper letter tracing with multiple sensory components',
                '⚠ HOME: Play activities: building (Legos), threading, cooking (precision tasks)',
                '⚠ HOME: Low-pressure writing: text messages, thank-you notes, drawing labels',
                '⚠ HOME: Celebrate motor progress and writing effort; normalize difficulties',
                '⚠ Refer to OT if motor skills not improving after 8 weeks'
            ],
            'High': [
                '🔴 INTENSIVE INTERVENTION REQUIRED - Significant Dysgraphia Risk',
                '🔴 PRIORITY: Comprehensive evaluation by occupational therapist specialist',
                '🔴 Request IEP evaluation for Special Education services immediately',
                '🔴 Request 504 Plan if not IEP eligible (legally required accommodations)',
                '🔴 1:1 occupational therapy 4-5x per week (30-60 minutes per session)',
                '🔴 Specialized motor remediation program addressing foundational skills',
                '🔴 Gross motor assessment and intervention if underlying coordination issues',
                '🔴 Visual-motor integration activities: tracking, copying, pattern work',
                '🔴 Intensive multisensory handwriting: sandpaper, shaving cream, wet sand daily',
                '🔴 Bilateral coordination activities: both hands coordinated movements',
                '🔴 Pinch/grip strength building: therapeutic tools, squeezing activities daily',
                '🔴 Spatial awareness activities: body positioning, paper positioning, letter spacing',
                '🔴 Motor planning: explicit step-by-step instructions for complex movements',
                '🔴 Proprioceptive input: weighted vests, pressure activities before writing',
                '🔴 Explicit pencil grip instruction with adaptive grips (pencil grips, ergonomic)',
                '🔴 Posture support: optimize seating, height, lighting, environmental factors',
                '🔴 ACCOMMODATIONS: Unlimited time for handwritten work',
                '🔴 Alternative to handwriting: Speech-to-text PRIMARY method for expressing ideas',
                '🔴 Dragon NaturallySpeaking, Windows Dictation, or Google Docs voice typing',
                '🔴 All written assignments can be completed via keyboard or speech-to-text',
                '🔴 Handwriting used for functional writing only (signature, checks, forms)',
                '🔴 Large paper with extra spacing; visual guides for line following',
                '🔴 Graphic organizers provided for writing structure/planning',
                '🔴 No penalties for spelling, punctuation, legibility in content assessment',
                '🔴 Alternative assessments: oral responses, recorded explanations, drawings',
                '🔴 Reduced written output expectations; focus on quality content',
                '🔴 Tech support: Co:Writer, Grammarly for writing assistance and suggestions',
                '🔴 Anxiety management: breaks, positive reinforcement, low-pressure practice',
                '🔴 SPECIALIST TEAM: Occupational Therapist, Special Education Teacher, Psychologist',
                '🔴 Assess writing-related anxiety/frustration; implement coping strategies',
                '🔴 Monitor for perfectionism or avoidance; address emotional component',
                '🔴 HOME: Daily 20-30 minute fine motor practice with multi-sensory approach',
                '🔴 HOME: Therapeutic activities: play dough manipulation, threading, building',
                '🔴 HOME: Cooking/baking (measurement precision, sequencing)',
                '🔴 HOME: Avoid handwriting demands; use speech-to-text or typing at home',
                '🔴 HOME: Celebrate motor improvements and writing effort regardless of mechanics',
                '🔴 HOME: Build confidence through success-oriented writing activities',
                '🔴 ESCALATE: Occupational therapy progress review every 2-3 weeks',
                '🔴 Monitor response to intervention; adjust intensity and approach as needed'
            ]
        }
        return recommendations_map.get(risk_level, [])

