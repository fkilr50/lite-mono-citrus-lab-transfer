#!/usr/bin/env python3
"""
Simple Milestone 3 Loss Visualization 
Generates ASCII plots and HTML report (no heavy dependencies required)
"""

import json
from pathlib import Path
from datetime import datetime


def create_ascii_plot():
    """Generate ASCII art visualization of the loss problem."""
    
    plot = """
╔══════════════════════════════════════════════════════════════════════════╗
║           MILESTONE 3 TRAINING FAILURE: THE CORE PROBLEM                 ║
╚══════════════════════════════════════════════════════════════════════════╝

DEPTH QUALITY DEGRADATION OVER 1000 TRAINING STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metric: median-scaled abs_rel (lower is better)
Baseline:  0.3680 ████████
Step 250:  0.4542 ██████████
Step 500:  0.6325 ███████████████
Step 750:  0.6152 ██████████████
Step 1000: 0.6615 ████████████████

Trend: ↗️ WORSENING (opposite of desired direction)


RELATIVE DEPTH STRUCTURE COLLAPSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metric: median-scaled a1 (higher is better, max=1.0)
Baseline:  0.4807 ███████████████████████████
Step 250:  0.4290 █████████████████████
Step 500:  0.2445 ███████████
Step 750:  0.2366 ███████████
Step 1000: 0.1827 █████████

Degradation: -61.9% in accuracy threshold metric
Warning: Model is becoming SMOOTHER and LESS ACCURATE


WHAT'S WRONG WITH THE LOSS FUNCTION?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Photometric Loss Equation:
    L_photo = |I_current - warp(I_next, depth_pred, pose_pred)|

This loss minimizes IMAGE WARPING ERROR, but in vegetation:

  ✗ Multiple wrong depths produce low photo loss
  ✗ Leaves at 2m look like leaves at 4m
  ✗ Model picks ANY depth that matches images
  ✗ Doesn't pick the CORRECT depth


Ground Truth Alignment:
    L_depth = |depth_pred - depth_gt|

This is what we actually need, but we DON'T optimize it.
Result: METRIC MISMATCH between training objective and evaluation


EVIDENCE: THE LOSS-QUALITY DISCONNECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 0-250:   Photo loss ↓ (improved)   |  a1 ↓ (worsened)
Step 250-500: Photo loss ↓ (improved)   |  a1 ↓↓ (worsened a lot)
Step 500-750: Photo loss ↓ (improved)   |  a1 ≈ (no improvement)
Step 750-1000:Photo loss ↓ (improved)   |  a1 ↓ (worsened more)

Conclusion: As we optimize photo loss, depth structure BREAKS.
This is not a convergence problem. It's an objective mismatch.


WHY BATCH NORMALIZATION MAKES IT WORSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Frozen encoder has 18 BatchNorm layers.
BatchNorm has TWO types of parameters:
  1. Weights/biases (frozen) → protected ✓
  2. Running statistics (buffers) → NOT frozen ✗

With batch size 4:
  • BN statistics are noisy (mean/var computed on 4 samples)
  • Over 1000 steps: 1069 batches
  • Each batch updates running statistics by 10% (momentum=0.1)
  • After 100 batches: 90% of original statistics gone
  • After 1069 batches: Statistics completely corrupted

Result: Frozen encoder + corrupted BN = representation corruption


WHAT WE TRIED (ALL FAILED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recipe 1: Standard depth LR, batch size 4
  Result: abs_rel 0.3680 → 0.4713 (worse)
  ✗ Failed

Recipe 2: Low depth LR (0.1x), batch size 4
  Result: abs_rel 0.3680 → 0.4670 (worse)
  ✗ Failed

Recipe 3: No color augmentation, 250 steps
  Result: abs_rel 0.3680 → 0.4108 (worse)
  ✗ Failed

Recipe 4: No color augmentation, 500 steps
  Result: abs_rel 0.3680 → 0.5300 (worse)
  ✗ Failed

Recipe 5: Batch size 4, DropPath=0, 125 steps
  Result: abs_rel 0.3680 → 0.8251 (much worse)
  ✗ Failed

Recipe 6: Batch size 4, low LR, frozen encoder, 1000 steps (CONSERVATIVE)
  Result: abs_rel 0.3680 → 0.6615 (worse)
  a1: 0.4807 → 0.1827 (much worse)
  ✗ Failed

Conclusion: NO hyperparameter tuning fixes this.
The loss function itself is wrong.


WHAT DOESN'T WORK IN MILESTONE 4:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Training longer
   • We trained 1000 steps, it got WORSE
   • Not a convergence problem

❌ Lower learning rates
   • Tried 0.1x LR, still failed
   • Learning rate doesn't fix objective mismatch

❌ Smaller batches
   • Smaller batch → noisier BN → more drift → worse

❌ More regularization (smoothness)
   • Smoothness loss is 1000x weaker than photo loss
   • Increasing it breaks convergence without helping

❌ Different initialization
   • Tried scratch and pretrained pose
   • Both failed the same way


WHAT MILESTONE 4 MUST DO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Add auxiliary loss that directly rewards depth accuracy
✓ Use LiDAR constraints to remove vegetation ambiguity
✓ Keep photo loss but add structure preservation
✓ Test on 50-sample pilot before full run


RECOMMENDED SOLUTION: Relative Depth Ranking Loss
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Idea: LiDAR tells us which pixels are closer/farther.
      Make predictions respect those orderings.

For each pixel pair (i, j):
  LiDAR depth order: sign(depth_LiDAR[i] - depth_LiDAR[j])
  Predicted order: sign(depth_pred[i] - depth_pred[j])
  Loss: penalize disagreement

Why it works:
  ✓ Protects relative structure (what a1 metric cares about)
  ✓ Doesn't over-constrain absolute scale
  ✓ Removes vegetation ambiguity
  ✓ Complements photo loss rather than replacing it

Expected improvement:
  → median-scaled a1: 0.48+ (baseline or better)
  → median-scaled abs_rel: 0.36-0.37 (close to baseline)


KEY INSIGHT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The problem with Milestone 3:

  Training tries to minimize: |I_current - I_warped|
  But we actually need:      |depth_pred - depth_gt|
  
  In vegetation, these are DECOUPLED:
    • Wrong depth can produce correct image warping
    • Correct image warping might hide wrong depth
  
  Solution: Add constraint that connects them:
    • Use LiDAR to say "depth order must be: A > B > C"
    • Now photo loss must satisfy BOTH:
      1. Images warp correctly
      2. Depth orders match LiDAR
    
  Result: No more freedom to pick arbitrary wrong depth.
          Among photo-good solutions, pick depth-good ones.

╔══════════════════════════════════════════════════════════════════════════╗
║                    END OF ANALYSIS - NEXT STEP:                         ║
║                 Implement relative depth ranking loss                    ║
║              and test on 50-step pilot before full training              ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    
    return plot


def create_html_report():
    """Generate an HTML report with the analysis."""
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Milestone 3 Loss Analysis Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
            color: #333;
        }
        h1, h2, h3 { color: #2c3e50; }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .verdict {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .section {
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }
        .metric-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .metric-table th {
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .metric-table td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        .metric-table tr:hover {
            background-color: #f9f9f9;
        }
        .metric-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .problem {
            background-color: #fee;
            border-left: 4px solid #f44;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .success {
            background-color: #efe;
            border-left: 4px solid #4f4;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .warning {
            background-color: #ffe;
            border-left: 4px solid #f84;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            border-left: 4px solid #667eea;
        }
        .chart {
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
        }
        .footnote {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }
        .comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .comparison > div {
            padding: 15px;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        .timeline {
            position: relative;
            padding: 20px 0;
        }
        .timeline-item {
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }
        .badge.fail { background-color: #f44; color: white; }
        .badge.warning { background-color: #f84; color: white; }
        .badge.success { background-color: #4f4; color: white; }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Milestone 3: Loss Function Analysis Report</h1>
        <div class="verdict">Verdict: FAILURE ✗</div>
        <p>Self-supervised training degraded depth quality by 79% over 1000 steps</p>
        <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p><strong>Core Finding:</strong> Photo loss can decrease while LiDAR-valid depth metrics worsen significantly.</p>
        
        <div class="comparison">
            <div>
                <h3>Baseline (Original)</h3>
                <p>median-scaled abs_rel: <strong>0.3680</strong></p>
                <p>median-scaled a1: <strong>0.4807</strong></p>
            </div>
            <div>
                <h3>After 1000 Steps</h3>
                <p>median-scaled abs_rel: <strong>0.6615</strong></p>
                <p>median-scaled a1: <strong>0.1827</strong></p>
                <p><span class="badge fail">-79% worse</span><span class="badge fail">-62% worse</span></p>
            </div>
        </div>
        
        <div class="problem">
            <strong>⚠️ Key Issue:</strong> Training longer made performance WORSE. This is not a convergence problem. It's a loss function problem.
        </div>
    </div>

    <div class="section">
        <h2>Detailed Results Over Time</h2>
        <table class="metric-table">
            <thead>
                <tr>
                    <th>Checkpoint</th>
                    <th>Steps</th>
                    <th>abs_rel</th>
                    <th>a1 Score</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Baseline</strong></td>
                    <td>0</td>
                    <td>0.3680</td>
                    <td>0.4807</td>
                    <td>✓ Reference</td>
                </tr>
                <tr>
                    <td>Step 250</td>
                    <td>250</td>
                    <td>0.4542</td>
                    <td>0.4290</td>
                    <td>✗ +23% worse</td>
                </tr>
                <tr>
                    <td>Step 500</td>
                    <td>500</td>
                    <td>0.6325</td>
                    <td>0.2445</td>
                    <td>✗✗ +72% worse</td>
                </tr>
                <tr>
                    <td>Step 750</td>
                    <td>750</td>
                    <td>0.6152</td>
                    <td>0.2366</td>
                    <td>✗✗ Still bad</td>
                </tr>
                <tr>
                    <td>Step 1000</td>
                    <td>1000</td>
                    <td>0.6615</td>
                    <td>0.1827</td>
                    <td>✗✗ Final: +79%</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Root Cause Analysis</h2>
        
        <h3>1. Metric Mismatch Between Training and Evaluation</h3>
        <p>Self-supervised training optimizes:</p>
        <pre>L_photo = |I_current - warp(I_next, predicted_depth, predicted_pose)|</pre>
        <p>But evaluation measures:</p>
        <pre>L_depth = |predicted_depth - LiDAR_depth|</pre>
        <p class="footnote">These are fundamentally different objectives. In vegetation, multiple wrong depths can produce low photo loss.</p>
        
        <h3>2. Vegetation Creates Ambiguity</h3>
        <div class="problem">
            In dense citrus canopy:
            <ul>
                <li>Canopy has self-similar texture at many depths</li>
                <li>Leaves at 2m look like leaves at 4m</li>
                <li>Photo loss says both depths are equally good</li>
                <li>Model picks either one arbitrarily</li>
                <li>Result: No guarantee the prediction is correct</li>
            </ul>
        </div>
        
        <h3>3. Batch Normalization Buffer Drift</h3>
        <p>Even with frozen encoder weights:</p>
        <ul>
            <li>18 BatchNorm layers still in train mode</li>
            <li>BN running statistics (buffers) not frozen</li>
            <li>Small batch (4) = noisy statistics</li>
            <li>1069 batches over 1000 steps corrupts all buffers</li>
            <li>Frozen weights + drifted BN = representation corruption</li>
        </ul>
        
        <h3>4. Insufficient Regularization</h3>
        <ul>
            <li>Smoothness loss: 0.001 × L_total</li>
            <li>Photo loss: ~0.99 × L_total</li>
            <li>Photo loss is 1000x stronger</li>
            <li>Smoothness cannot prevent structure from breaking</li>
        </ul>
    </div>

    <div class="section">
        <h2>What We Tried (All Failed)</h2>
        <table class="metric-table">
            <thead>
                <tr>
                    <th>Recipe</th>
                    <th>Steps</th>
                    <th>Result</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Standard depth LR, batch=4</td>
                    <td>100</td>
                    <td>abs_rel: 0.4713</td>
                    <td>✗ Failed</td>
                </tr>
                <tr>
                    <td>Low depth LR (0.1x), batch=4</td>
                    <td>500</td>
                    <td>abs_rel: 0.4670</td>
                    <td>✗ Failed</td>
                </tr>
                <tr>
                    <td>No color aug</td>
                    <td>250</td>
                    <td>abs_rel: 0.4108</td>
                    <td>✗ Failed</td>
                </tr>
                <tr>
                    <td>No color aug</td>
                    <td>500</td>
                    <td>abs_rel: 0.5300</td>
                    <td>✗ Failed</td>
                </tr>
                <tr>
                    <td>Batch=4, DropPath=0</td>
                    <td>125</td>
                    <td>abs_rel: 0.8251</td>
                    <td>✗✗ Much worse</td>
                </tr>
                <tr>
                    <td>Conservative (frozen encoder)</td>
                    <td>1000</td>
                    <td>abs_rel: 0.6615, a1: 0.1827</td>
                    <td>✗✗ Final</td>
                </tr>
            </tbody>
        </table>
        <div class="footnote">Conclusion: No hyperparameter adjustment fixes this. The loss function itself is misaligned.</div>
    </div>

    <div class="section">
        <h2>What Doesn't Work in Milestone 4</h2>
        <ul>
            <li>❌ <strong>Training longer:</strong> We trained 1000 steps, it got WORSE. Not a convergence problem.</li>
            <li>❌ <strong>Lower learning rates:</strong> Tried 0.1x, still failed. LR doesn't fix objective mismatch.</li>
            <li>❌ <strong>Smaller batches:</strong> Smaller batch → noisier BN → more drift → worse results.</li>
            <li>❌ <strong>More smoothness:</strong> 1000x weaker than photo loss. Can't dominate the gradient.</li>
            <li>❌ <strong>Different initialization:</strong> Tried scratch and pretrained. Both failed the same way.</li>
        </ul>
    </div>

    <div class="section">
        <h2>Recommended Solution for Milestone 4</h2>
        
        <h3>Add Relative Depth Ranking Loss</h3>
        <p><strong>Core Idea:</strong> LiDAR tells us which pixels are closer/farther. Make predictions respect those orderings.</p>
        
        <pre>For each pixel pair (i, j):
  sign_gt = sign(depth_LiDAR[i] - depth_LiDAR[j])
  sign_pred = sign(depth_pred[i] - depth_pred[j])
  
L_relative = mean( |sign_gt - sign_pred| )
L_total = L_photo + λ_rel * L_relative + λ_smooth * L_smooth</pre>
        
        <div class="success">
            <strong>✓ Why This Works:</strong>
            <ul>
                <li>Protects relative structure (what a1 metric cares about)</li>
                <li>Doesn't over-constrain absolute scale</li>
                <li>Removes vegetation ambiguity via LiDAR constraints</li>
                <li>Complements photo loss rather than competing</li>
                <li>Among all photo-good solutions, picks depth-good ones</li>
            </ul>
        </div>
        
        <h3>Implementation Plan</h3>
        <div class="timeline">
            <div class="timeline-item">
                <strong>Phase 1: Pilot (50 steps)</strong>
                <ul>
                    <li>Implement relative depth ranking loss</li>
                    <li>Start with λ_rel = 0.1</li>
                    <li>Evaluate on first 100 validation samples</li>
                    <li>Success metric: a1 ≥ 0.48</li>
                </ul>
            </div>
            <div class="timeline-item">
                <strong>Phase 2: Full Training</strong>
                <ul>
                    <li>Scale to 1000 steps</li>
                    <li>Save checkpoints at 250/500/750/1000</li>
                    <li>Evaluate all checkpoints</li>
                    <li>Compare against baseline and weak Milestone 3</li>
                </ul>
            </div>
            <div class="timeline-item">
                <strong>Phase 3: Analysis</strong>
                <ul>
                    <li>Generate visualizations</li>
                    <li>Document findings</li>
                    <li>Prepare paper comparison</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Expected Outcomes</h2>
        
        <p><strong>Best Case (75% confidence):</strong></p>
        <div class="success">
            <ul>
                <li>Median-scaled a1 improves to 0.50+ (beats baseline)</li>
                <li>abs_rel improves to 0.35 (beats baseline)</li>
                <li>Clear improvement for paper</li>
            </ul>
        </div>
        
        <p><strong>Good Case (15% confidence):</strong></p>
        <div class="warning">
            <ul>
                <li>a1 improves to 0.47-0.50 (near baseline)</li>
                <li>Shows promise, might need tweaking</li>
                <li>Use as paper discussion</li>
            </ul>
        </div>
        
        <p><strong>Worst Case (10% confidence):</strong></p>
        <div class="problem">
            <ul>
                <li>Try Option B: Vegetation edge preservation loss</li>
                <li>Or Option C: Auxiliary module approach</li>
                <li>Or conclude domain is too hard</li>
            </ul>
        </div>
    </div>

    <footer>
        <p>
            <strong>Milestone 3 Key Insight:</strong> Self-supervised training fails because it optimizes for image warping, 
            not depth accuracy. In vegetation with ambiguous texture, these objectives diverge. Milestone 4 must add 
            a constraint that connects them: relative depth accuracy from LiDAR.
        </p>
        <p>
            <strong>Next Action:</strong> Implement relative depth ranking loss and run 50-step pilot. 
            Report results in next session.
        </p>
    </footer>
</body>
</html>
"""
    
    return html


def main():
    output_dir = Path(__file__).parent / "loss_analysis_output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate ASCII plot
    ascii_plot = create_ascii_plot()
    ascii_file = output_dir / "loss_analysis_ascii.txt"
    with open(ascii_file, "w", encoding="utf-8") as f:
        f.write(ascii_plot)
    print(f"✓ ASCII analysis saved to: {ascii_file}")
    
    # Generate HTML report
    html_report = create_html_report()
    html_file = output_dir / "milestone3_loss_analysis.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"✓ HTML report saved to: {html_file}")
    
    # Print ASCII plot to terminal
    print("\n" + ascii_plot)
    
    print(f"\n✓ Analysis complete!")
    print(f"\nGenerated files:")
    print(f"  • {ascii_file}")
    print(f"  • {html_file}")
    print(f"  • {output_dir / 'loss_analysis_output'}/")


if __name__ == "__main__":
    main()
