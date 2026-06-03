#!/usr/bin/env python3
"""Risk quantification and analysis for OpenExec."""

from typing import Dict, Any, List


class RiskQuantifier:
    """Quantifies risks with probability and impact scoring."""

    def __init__(self):
        self.risk_patterns = {
            'burn': {'probability': 0.7, 'impact': 8},
            'runway': {'probability': 0.6, 'impact': 9},
            'bankrupt': {'probability': 0.4, 'impact': 10},
            'obsolescence': {'probability': 0.5, 'impact': 6},
            'debt': {'probability': 0.6, 'impact': 7},
            'market': {'probability': 0.5, 'impact': 7},
            'competitive': {'probability': 0.4, 'impact': 6},
            'regulatory': {'probability': 0.3, 'impact': 8},
        }

    def quantify_risk(self, risk_text: str) -> Dict[str, Any]:
        """Quantify a single risk based on text analysis."""
        risk_lower = risk_text.lower()

        # Default values
        probability = 0.5
        impact = 5
        mitigation_cost = "Medium"

        # Check for patterns
        for pattern, scores in self.risk_patterns.items():
            if pattern in risk_lower:
                probability = scores['probability']
                impact = scores['impact']
                break

        # Adjust based on agent (CEO/CFO risks are typically higher impact)
        if '[CEO]' in risk_text or '[CFO]' in risk_text:
            impact = min(10, impact + 1)

        # Calculate risk score
        risk_score = probability * impact

        return {
            'text': risk_text,
            'probability': probability,
            'impact': impact,
            'risk_score': risk_score,
            'mitigation_cost': mitigation_cost,
            'priority': self._get_priority(risk_score)
        }

    def _get_priority(self, risk_score: float) -> str:
        """Get priority based on risk score."""
        if risk_score >= 7:
            return "HIGH"
        elif risk_score >= 4:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_risk_matrix(self, risks: List[str]) -> str:
        """Generate ASCII risk matrix."""
        quantified = [self.quantify_risk(risk) for risk in risks]

        matrix = []
        matrix.append("Risk Matrix:")
        matrix.append("            IMPACT →")
        matrix.append("            Low   Med   High  Critical")
        matrix.append("PROBABIL  High  .     .     [H]   [C]")
        matrix.append("ITY    ↑  Med   .     [M]   [H]   [C]")
        matrix.append("         Low   [L]   [M]   [H]   .")

        matrix.append("")
        matrix.append("Legend: [L]=Low, [M]=Medium, [H]=High, [C]=Critical")
        matrix.append("")

        # Add detailed breakdown
        matrix.append("## Quantified Risks")
        matrix.append("")
        for risk in sorted(quantified, key=lambda x: x['risk_score'], reverse=True)[:10]:
            matrix.append(f"- {risk['priority']} | P:{risk['probability']:.0%} | I:{risk['impact']}/10 | Score:{risk['risk_score']:.1f}")
            matrix.append(f"  {risk['text'][:80]}...")
            matrix.append("")

        return '\n'.join(matrix)


def quantify_risks(results: Dict[str, Any]) -> Dict[str, Any]:
    """Add risk quantification to results."""
    quantifier = RiskQuantifier()

    all_risks = results.get('overall_risk_assessment', [])
    quantified_risks = [quantifier.quantify_risk(risk) for risk in all_risks]

    # Sort by risk score
    quantified_risks.sort(key=lambda x: x['risk_score'], reverse=True)

    results['quantified_risks'] = quantified_risks
    results['risk_matrix'] = quantifier.generate_risk_matrix(all_risks)

    return results