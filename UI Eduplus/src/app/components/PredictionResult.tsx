import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Brain, ArrowLeft, TrendingUp, Trophy, Download, BarChart2, ChevronDown, ChevronUp } from "lucide-react";
import { Link } from "react-router";
import { motion } from "motion/react";
import { StudentSession } from "../auth";
import { jsPDF } from "jspdf";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const EDUPLUS_LOGO_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="260" height="80" viewBox="0 0 260 80">
  <rect width="260" height="80" fill="#ffffff"/>
  <text x="10" y="48" font-family="Verdana, Arial, sans-serif" font-size="44" font-weight="700" fill="#2B3FC0">eduplus</text>
  <rect x="170" y="45" width="80" height="25" rx="6" fill="#F59E0B"/>
  <text x="180" y="63" font-family="Verdana, Arial, sans-serif" font-size="22" font-style="italic" fill="#ffffff">campus</text>
</svg>
`;

async function getEduplusLogoPngDataUrl(): Promise<string> {
  const blob = new Blob([EDUPLUS_LOGO_SVG], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  try {
    const pngData = await new Promise<string>((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = 260;
        canvas.height = 80;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("Could not create canvas context"));
          return;
        }
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/png"));
      };
      img.onerror = () => reject(new Error("Failed to load logo SVG"));
      img.src = url;
    });

    return pngData;
  } finally {
    URL.revokeObjectURL(url);
  }
}

interface Predictions {
  student_id: number;
  overall_placement_probability: number;
  predicted_salary_lpa: number;
  salary_range_min_lpa: number;
  salary_range_mid_lpa: number;
  salary_range_max_lpa: number;
  prob_salary_gt_2_lpa: number;
  prob_salary_gt_5_lpa: number;
  prob_salary_gt_10_lpa: number;
  prob_salary_gt_15_lpa: number;
  prob_salary_gt_20_lpa: number;
  prob_salary_gt_25_lpa: number;
  prob_salary_gt_30_lpa: number;
  prob_salary_gt_35_lpa: number;
  prob_salary_gt_40_lpa: number;
  predicted_job_role: string;
  recommended_companies: string;
  is_low_probability_case?: boolean;
  low_probability_report_json?: string;
  low_probability_report?: {
    is_low_probability_case?: boolean;
    threshold_pct?: number;
    current_probability_pct?: number;
    summary?: string;
    final_note?: string;
    data_snapshot?: Record<string, number | string>;
    reasons?: Array<{
      parameter: string;
      current: number;
      target: number;
      gap: number;
      impact: string;
      why_it_matters: string;
    }>;
    practical_changes?: Array<{
      focus_area: string;
      action: string;
      target: string;
      timeline: string;
    }>;
    peer_comparison?: {
      available?: boolean;
      message?: string;
      bottom_bucket_statement?: string;
      student_percentiles?: {
        technical_percentile?: number;
        dsa_percentile?: number;
        project_percentile?: number;
      };
      top_25_percent_thresholds?: {
        dsa_score_q75?: number;
        project_score_q75?: number;
        technical_score_q75?: number;
      };
    };
    confidence_reliability?: {
      available?: boolean;
      confidence_label?: string;
      uncertainty_pct?: number;
      reason?: string;
      nearest_profile_distance?: number;
      distance_normalized?: number;
    };
    risk_alerts?: Array<{
      severity: string;
      title: string;
      risk: string;
    }>;
    projected_improvement?: {
      available?: boolean;
      simulation_note?: string;
      changes_assumed?: {
        dsa_score?: { current?: number; projected?: number };
        project_score?: { current?: number; projected?: number };
      };
      placement_probability?: { current?: number; projected?: number; delta?: number };
      predicted_salary_lpa?: { current?: number; projected?: number; delta?: number };
    };
  };
}

interface PredictionResultProps {
  session: StudentSession;
}

export function PredictionResult({ session }: PredictionResultProps) {
  const [predictions, setPredictions] = useState<Predictions | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSalaries, setExpandedSalaries] = useState(false);
  const [studentsLoaded, setStudentsLoaded] = useState(false);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/predictions/${session.studentId}`);
        const data = await res.json();
        if (data.predictions) {
          const normalized = { ...data.predictions } as Predictions;

          if (!normalized.low_probability_report && typeof normalized.low_probability_report_json === "string" && normalized.low_probability_report_json.trim()) {
            try {
              normalized.low_probability_report = JSON.parse(normalized.low_probability_report_json);
            } catch {
              normalized.low_probability_report = undefined;
            }
          }

          setPredictions(normalized);
          localStorage.setItem('lastStudentId', session.studentId.toString());
          setStudentsLoaded(true);
        }
      } catch (err) {
        console.error("Error fetching predictions:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
  }, [session.studentId]);

  const companies = predictions?.recommended_companies 
    ? predictions.recommended_companies.split(',').map(c => c.trim()).filter(c => c)
    : [];

  const salaryThresholds = [
    { label: ">2 LPA", value: predictions?.prob_salary_gt_2_lpa || 0 },
    { label: ">5 LPA", value: predictions?.prob_salary_gt_5_lpa || 0 },
    { label: ">10 LPA", value: predictions?.prob_salary_gt_10_lpa || 0 },
    { label: ">15 LPA", value: predictions?.prob_salary_gt_15_lpa || 0 },
    { label: ">20 LPA", value: predictions?.prob_salary_gt_20_lpa || 0 },
    { label: ">25 LPA", value: predictions?.prob_salary_gt_25_lpa || 0 },
    { label: ">30 LPA", value: predictions?.prob_salary_gt_30_lpa || 0 },
    { label: ">35 LPA", value: predictions?.prob_salary_gt_35_lpa || 0 },
    { label: ">40 LPA", value: predictions?.prob_salary_gt_40_lpa || 0 },
  ];

  const isLowProbabilityCase = !!predictions && (
    !!predictions.is_low_probability_case ||
    Number(predictions.overall_placement_probability) < 30
  );

  const lowReport = predictions?.low_probability_report;

  const downloadPredictionReport = async () => {
    if (!predictions) return;

    const doc = new jsPDF({ unit: "mm", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 14;
    const contentWidth = pageWidth - margin * 2;
    const reportDate = new Date().toLocaleString();
    let y = 16;

    const COLORS = {
      blueHeader: [11, 88, 176] as [number, number, number],
      blueCard: [239, 246, 255] as [number, number, number],
      redHeader: [185, 28, 28] as [number, number, number],
      redCard: [254, 242, 242] as [number, number, number],
      orangeHeader: [194, 65, 12] as [number, number, number],
      orangeCard: [255, 247, 237] as [number, number, number],
      greenHeader: [22, 163, 74] as [number, number, number],
      greenCard: [240, 253, 244] as [number, number, number],
      grayBorder: [203, 213, 225] as [number, number, number],
      text: [17, 24, 39] as [number, number, number],
      mutedText: [71, 85, 105] as [number, number, number],
    };

    const ensureSpace = (needed = 8) => {
      if (y + needed > pageHeight - 14) {
        doc.addPage();
        y = 16;
      }
    };

    const addWrappedText = (
      text: string,
      fontSize = 10.5,
      x = margin,
      maxWidth = contentWidth,
      lineHeight = 5,
      color: [number, number, number] = COLORS.text,
      style: "normal" | "bold" = "normal"
    ) => {
      doc.setFont("helvetica", style);
      doc.setFontSize(fontSize);
      doc.setTextColor(...color);
      const lines = doc.splitTextToSize(text, maxWidth);
      lines.forEach((line: string) => {
        ensureSpace(lineHeight);
        doc.text(line, x, y);
        y += lineHeight;
      });
      doc.setFont("helvetica", "normal");
    };

    const estimateWrappedHeight = (text: string, maxWidth: number, fontSize = 10, lineHeight = 4.8) => {
      doc.setFontSize(fontSize);
      const lines = doc.splitTextToSize(text || "-", maxWidth);
      return Math.max(1, lines.length) * lineHeight;
    };

    const drawCardSection = (
      title: string,
      headerColor: [number, number, number],
      cardColor: [number, number, number],
      contentHeight: number,
      drawContent: (x: number, startY: number, width: number) => void
    ) => {
      const headerH = 8;
      const pad = 2.5;
      const totalH = headerH + pad + contentHeight + pad;
      ensureSpace(totalH + 2);

      const sectionTop = y;

      doc.setFillColor(...cardColor);
      doc.setDrawColor(...COLORS.grayBorder);
      doc.roundedRect(margin, sectionTop, contentWidth, totalH, 2, 2, "FD");

      doc.setFillColor(...headerColor);
      doc.roundedRect(margin, sectionTop, contentWidth, headerH, 2, 2, "F");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(11.5);
      doc.setTextColor(255, 255, 255);
      doc.text(title, margin + 3, sectionTop + 5.5);

      const contentStartY = sectionTop + headerH + pad + 0.5;
      y = contentStartY;
      drawContent(margin + 3, contentStartY, contentWidth - 6);

      y = sectionTop + totalH + 1.5;
      doc.setFont("helvetica", "normal");
    };

    const drawTable = (
      columns: string[],
      rows: string[][],
      colWidths: number[],
      headerColor: [number, number, number],
      bodyTextColor: [number, number, number] = COLORS.text,
      headerTextColor: [number, number, number] = [255, 255, 255]
    ) => {
      const tableX = margin + 3;
      const tableWidth = contentWidth - 6;
      const headerH = 7;
      const cellPadX = 1.5;
      const cellPadY = 1.8;
      const fontSize = 9.2;
      const lineHeight = 4.5;

      const totalWeight = colWidths.reduce((a, b) => a + b, 0);
      const absWidths = colWidths.map((w) => (w / totalWeight) * tableWidth);

      const rowHeights = rows.map((row) => {
        let h = 6;
        row.forEach((cell, idx) => {
          const txtW = Math.max(10, absWidths[idx] - cellPadX * 2);
          h = Math.max(h, estimateWrappedHeight(cell || "-", txtW, fontSize, lineHeight) + cellPadY * 2);
        });
        return h;
      });

      const totalH = headerH + rowHeights.reduce((a, b) => a + b, 0);
      ensureSpace(totalH + 2);

      doc.setFillColor(...headerColor);
      doc.setDrawColor(...COLORS.grayBorder);
      doc.rect(tableX, y, tableWidth, headerH, "FD");

      let xCursor = tableX;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9.2);
      doc.setTextColor(...headerTextColor);
      columns.forEach((col, idx) => {
        const w = absWidths[idx];
        doc.text(col, xCursor + cellPadX, y + 4.7);
        if (idx < columns.length - 1) {
          doc.line(xCursor + w, y, xCursor + w, y + headerH);
        }
        xCursor += w;
      });

      let rowY = y + headerH;
      rows.forEach((row, rowIdx) => {
        const h = rowHeights[rowIdx];
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(...COLORS.grayBorder);
        doc.rect(tableX, rowY, tableWidth, h, "FD");

        let cellX = tableX;
        row.forEach((cell, cIdx) => {
          const w = absWidths[cIdx];
          const txtW = Math.max(10, w - cellPadX * 2);
          const lines = doc.splitTextToSize(cell || "-", txtW);
          doc.setFont("helvetica", cIdx === 4 && /\d+(\.\d+)?/.test(cell || "") ? "bold" : "normal");
          doc.setFontSize(fontSize);
          doc.setTextColor(...bodyTextColor);
          let txtY = rowY + cellPadY + 3.2;
          lines.forEach((ln: string) => {
            doc.text(ln, cellX + cellPadX, txtY);
            txtY += lineHeight;
          });

          if (cIdx < row.length - 1) {
            doc.line(cellX + w, rowY, cellX + w, rowY + h);
          }
          cellX += w;
        });
        rowY += h;
      });

      y = rowY + 1;
      doc.setFont("helvetica", "normal");
    };

    const estimateTableHeight = (rows: string[][], colWidths: number[]) => {
      const tableWidth = contentWidth - 6;
      const headerH = 7;
      const cellPadX = 1.5;
      const cellPadY = 1.8;
      const fontSize = 9.2;
      const lineHeight = 4.5;

      const totalWeight = colWidths.reduce((a, b) => a + b, 0);
      const absWidths = colWidths.map((w) => (w / totalWeight) * tableWidth);

      const rowHeights = rows.map((row) => {
        let h = 6;
        row.forEach((cell, idx) => {
          const txtW = Math.max(10, absWidths[idx] - cellPadX * 2);
          h = Math.max(h, estimateWrappedHeight(cell || "-", txtW, fontSize, lineHeight) + cellPadY * 2);
        });
        return h;
      });

      return headerH + rowHeights.reduce((a, b) => a + b, 0) + 1;
    };

    doc.setFillColor(0, 51, 102);
    doc.rect(0, 0, pageWidth, 28, "F");

    try {
      const logoData = await getEduplusLogoPngDataUrl();
      doc.addImage(logoData, "PNG", margin, 5, 44, 13.5);
    } catch {
      doc.setFontSize(16);
      doc.setTextColor(255, 255, 255);
      doc.text("Eduplus Campus", margin, 14);
    }

    doc.setFontSize(16);
    doc.setTextColor(255, 255, 255);
    doc.text("My Prediction Report", pageWidth - margin, 13, { align: "right" });

    y = 36;
    drawCardSection(
      "Report Summary",
      COLORS.blueHeader,
      COLORS.blueCard,
      28,
      (x, startY, width) => {
        y = startY;
        addWrappedText(`Student ID: ${session.studentId}`, 10.5, x, width, 5, COLORS.text);
        addWrappedText(`Generated On: ${reportDate}`, 10.5, x, width, 5, COLORS.text);
        addWrappedText(`Placement Probability: ${predictions.overall_placement_probability}%`, 10.8, x, width, 5, COLORS.redHeader, "bold");
        addWrappedText(
          `Probability Band: ${predictions.overall_placement_probability >= 80 ? "High" : predictions.overall_placement_probability >= 60 ? "Good" : predictions.overall_placement_probability >= 40 ? "Moderate" : "Low"}`,
          10.5,
          x,
          width,
          5,
          COLORS.text
        );
      }
    );

    if (isLowProbabilityCase) {
      const reasonsRows = (lowReport?.reasons || []).map((r) => [
        String(r.parameter || "-"),
        String(r.impact || "-"),
        String(r.current ?? "-"),
        String(r.target ?? "-"),
        String(r.gap ?? "-"),
        String(r.why_it_matters || "-"),
      ]);

      const reasonsIntro = lowReport?.summary || "Your prediction is below 30% due to high-impact gaps in key placement parameters.";
      const reasonsIntroH = estimateWrappedHeight(reasonsIntro, contentWidth - 12, 10.2, 5);
      const reasonsTableRows = reasonsRows.length ? reasonsRows : [["-", "-", "-", "-", "-", "-"]];
      const reasonsTableH = estimateTableHeight(reasonsTableRows, [20, 8, 8, 8, 8, 24]);
      drawCardSection(
        "Why Probability Is Low",
        COLORS.redHeader,
        COLORS.redCard,
        reasonsIntroH + reasonsTableH + 3,
        (x, startY, width) => {
          y = startY;
          addWrappedText(reasonsIntro, 10.2, x, width, 5, COLORS.text);
          drawTable(
            ["Factor", "Impact", "Current", "Target", "Gap", "Reason"],
            reasonsTableRows,
            [20, 8, 8, 8, 8, 24],
            COLORS.redHeader
          );
        }
      );

      const practicalRows = (lowReport?.practical_changes || []).map((p) => [
        String(p.focus_area || "-"),
        String(p.action || "-"),
        String(p.target || "-"),
        String(p.timeline || "-"),
      ]);
      const practicalTableRows = practicalRows.length ? practicalRows : [["-", "-", "-", "-"]];
      const practicalH = estimateTableHeight(practicalTableRows, [16, 34, 20, 12]);
      drawCardSection(
        "Practical Changes You Should Do",
        COLORS.orangeHeader,
        COLORS.orangeCard,
        practicalH + 2,
        () => {
          drawTable(
            ["Area", "Action", "Target", "Timeline"],
            practicalTableRows,
            [16, 34, 20, 12],
            COLORS.orangeHeader
          );
        }
      );

      const modelRows = Object.entries(lowReport?.data_snapshot || {}).map(([k, v]) => [
        String(k.replace(/_/g, " ")),
        String(v),
      ]);
      const modelTableRows = modelRows.length ? modelRows : [["-", "-"]];
      const modelH = estimateTableHeight(modelTableRows, [40, 20]);
      drawCardSection(
        "Model Data Snapshot",
        COLORS.blueHeader,
        COLORS.blueCard,
        modelH + 2,
        () => {
          drawTable(
            ["Metric", "Value"],
            modelTableRows,
            [40, 20],
            COLORS.blueHeader
          );
        }
      );

      const peerMsg = lowReport?.peer_comparison?.bottom_bucket_statement || lowReport?.peer_comparison?.message || "Peer comparison not available.";
      const peerRows = [
        ["Top 25% DSA", String(lowReport?.peer_comparison?.top_25_percent_thresholds?.dsa_score_q75 ?? "N/A")],
        ["Top 25% Projects", String(lowReport?.peer_comparison?.top_25_percent_thresholds?.project_score_q75 ?? "N/A")],
        ["Top 25% Technical", String(lowReport?.peer_comparison?.top_25_percent_thresholds?.technical_score_q75 ?? "N/A")],
      ];
      const peerMsgH = estimateWrappedHeight(peerMsg, contentWidth - 12, 10.2, 5);
      const peerTableH = estimateTableHeight(peerRows, [40, 20]);
      drawCardSection(
        "Peer Comparison",
        COLORS.blueHeader,
        COLORS.blueCard,
        peerMsgH + peerTableH + 3,
        (x, startY, width) => {
          y = startY;
          addWrappedText(peerMsg, 10.2, x, width, 5, COLORS.text);
          drawTable(["Metric", "Value"], peerRows, [40, 20], COLORS.blueHeader);
        }
      );

      const c = lowReport?.confidence_reliability;
      const confRows = [
        ["Prediction Confidence", `${c?.confidence_label || "Unknown"}${typeof c?.uncertainty_pct === "number" ? ` (±${c.uncertainty_pct}%)` : ""}`],
        ["Reason", String(c?.reason || "Insufficient data similarity information.")],
      ];
      const confH = estimateTableHeight(confRows, [26, 34]);
      drawCardSection(
        "Confidence and Reliability",
        COLORS.blueHeader,
        COLORS.blueCard,
        confH + 2,
        () => {
          drawTable(["Metric", "Value"], confRows, [26, 34], COLORS.blueHeader);
        }
      );

      const riskRows = (lowReport?.risk_alerts || []).length
        ? (lowReport?.risk_alerts || []).map((r) => [
            String(r.severity || "-"),
            String(r.title || "-"),
            String(r.risk || "-"),
          ])
        : [["-", "-", "No critical risk alerts generated from current data."]];
      const riskH = estimateTableHeight(riskRows, [12, 20, 28]);
      drawCardSection(
        "Risk Alerts",
        COLORS.redHeader,
        COLORS.redCard,
        riskH + 2,
        () => {
          drawTable(["Severity", "Risk", "Details"], riskRows, [12, 20, 28], COLORS.redHeader);
        }
      );

      const p = lowReport?.projected_improvement;
      const projectedRows = p?.placement_probability && p?.predicted_salary_lpa
        ? [
            ["Placement Probability", `${p.placement_probability.current}%`, `${p.placement_probability.projected}%`, `${p.placement_probability.delta}%`],
            ["Predicted Salary", `${p.predicted_salary_lpa.current} LPA`, `${p.predicted_salary_lpa.projected} LPA`, `${p.predicted_salary_lpa.delta} LPA`],
          ]
        : [["Projected improvement impact", "-", "-", "Unavailable"]];

      const projectedNote = p?.simulation_note || "Projected improvement impact is currently unavailable.";
      const projectedNoteH = estimateWrappedHeight(projectedNote, contentWidth - 12, 10.2, 5);
      const projectedH = estimateTableHeight(projectedRows, [26, 12, 12, 10]);
      drawCardSection(
        "Projected Improvement Impact",
        COLORS.greenHeader,
        COLORS.greenCard,
        projectedH + projectedNoteH + 3,
        (x, startY, width) => {
          y = startY;
          drawTable(["Metric", "Current", "Improved", "Delta"], projectedRows, [26, 12, 12, 10], COLORS.greenHeader);
          y += 2;
          addWrappedText(projectedNote, 10, x, width, 5, COLORS.mutedText);
        }
      );

      drawCardSection(
        "How To Increase Your Prediction",
        COLORS.greenHeader,
        COLORS.greenCard,
        estimateWrappedHeight(lowReport?.final_note || "If you implement all the above changes consistently, your prediction can improve in the next cycle.", contentWidth - 12, 10.5, 5) + 2,
        (x, startY, width) => {
          y = startY;
          addWrappedText(lowReport?.final_note || "If you implement all the above changes consistently, your prediction can improve in the next cycle.", 10.5, x, width, 5, COLORS.text);
        }
      );
    } else {
      drawCardSection(
        "Salary Prediction",
        COLORS.greenHeader,
        COLORS.greenCard,
        estimateWrappedHeight(`Predicted Salary: INR ${predictions.predicted_salary_lpa} LPA`, contentWidth - 12, 10.5, 5)
          + estimateWrappedHeight(`Salary Range: INR ${predictions.salary_range_min_lpa} - INR ${predictions.salary_range_max_lpa} LPA`, contentWidth - 12, 10.5, 5)
          + estimateWrappedHeight(`Mid Range: INR ${predictions.salary_range_mid_lpa} LPA`, contentWidth - 12, 10.5, 5)
          + 2,
        (x, startY, width) => {
          y = startY;
          addWrappedText(`Predicted Salary: INR ${predictions.predicted_salary_lpa} LPA`, 10.5, x, width, 5, COLORS.text);
          addWrappedText(`Salary Range: INR ${predictions.salary_range_min_lpa} - INR ${predictions.salary_range_max_lpa} LPA`, 10.5, x, width, 5, COLORS.text);
          addWrappedText(`Mid Range: INR ${predictions.salary_range_mid_lpa} LPA`, 10.5, x, width, 5, COLORS.text);
        }
      );

      drawCardSection(
        "Cumulative Salary Probabilities",
        COLORS.blueHeader,
        COLORS.blueCard,
        estimateTableHeight(salaryThresholds.map((row) => [row.label, `${row.value}%`]), [40, 20]) + 2,
        () => {
          drawTable(
            ["Metric", "Value"],
            salaryThresholds.map((row) => [row.label, `${row.value}%`]),
            [40, 20],
            COLORS.blueHeader
          );
        }
      );

      drawCardSection(
        "Predicted Job Role",
        COLORS.blueHeader,
        COLORS.blueCard,
        estimateWrappedHeight(predictions.predicted_job_role || "Not available", contentWidth - 12, 10.5, 5) + 2,
        (x, startY, width) => {
          y = startY;
          addWrappedText(predictions.predicted_job_role || "Not available", 10.5, x, width, 5, COLORS.text);
        }
      );

      const reportCompanies = companies.length ? companies : ["No recommendation available"];
      drawCardSection(
        "Recommended Companies",
        COLORS.blueHeader,
        COLORS.blueCard,
        9 + reportCompanies.length * 7,
        () => {
          drawTable(
            ["#", "Company"],
            reportCompanies.map((c, idx) => [`${idx + 1}`, c]),
            [10, 50],
            COLORS.blueHeader
          );
        }
      );

      drawCardSection(
        "How To Increase Your Prediction",
        COLORS.greenHeader,
        COLORS.greenCard,
        estimateWrappedHeight("Keep improving DSA, project quality, CS fundamentals, aptitude, HR, ATS score, and interview consistency.", contentWidth - 12, 10.5, 5) + 2,
        (x, startY, width) => {
          y = startY;
          addWrappedText("Keep improving DSA, project quality, CS fundamentals, aptitude, HR, ATS score, and interview consistency.", 10.5, x, width, 5, COLORS.text);
        }
      );
    }

    const totalPages = doc.getNumberOfPages();
    for (let page = 1; page <= totalPages; page += 1) {
      doc.setPage(page);
      doc.setFontSize(9);
      doc.setTextColor(120, 120, 120);
      doc.text(`Eduplus Placement Report | Page ${page} of ${totalPages}`, pageWidth - margin, pageHeight - 6, { align: "right" });
    }

    doc.save(`prediction-report-${session.studentId}.pdf`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center">
        <div className="animate-spin mb-4">
          <div className="w-16 h-16 border-4 border-[#003366]/20 border-t-[#003366] rounded-full"></div>
        </div>
        <p className="text-lg font-medium">Loading predictions...</p>
      </div>
    );
  }

  if (!predictions || !studentsLoaded) {
    return (
      <div className="min-h-screen bg-background">
        <header className="bg-card border-b border-border px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Link to="/dashboard">
              <Button variant="ghost">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#003366] to-[#0055A4] rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl" style={{ fontWeight: 700 }}>PlacementAI</h1>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-12">
          <Card className="p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold mb-2">No Predictions Yet</h2>
            <p className="text-muted-foreground mb-6">
              Start by generating your placement probability prediction to see your results here.
            </p>
            <Link to="/placement-probability">
              <Button className="bg-gradient-to-r from-[#003366] to-[#0055A4] hover:opacity-90 h-12 px-6">
                Generate Prediction
              </Button>
            </Link>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background from-50% to-[#003366]/3">
      {/* Header */}
      <header className="bg-card border-b border-border px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/dashboard">
            <Button variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#003366] to-[#0055A4] rounded-xl flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl" style={{ fontWeight: 700 }}>My Predictions</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12 space-y-12">
        {/* Top Section - Probability */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="p-12 text-center bg-gradient-to-br from-[#003366] to-[#0055A4] text-white border-none shadow-xl">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Trophy className="w-8 h-8 text-[#FFC107]" />
              <h2 className="text-2xl" style={{ fontWeight: 600 }}>Your Placement Probability</h2>
            </div>
            
            <div className="relative inline-block mb-6">
              <svg className="w-64 h-64" viewBox="0 0 200 200">
                <circle
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="16"
                />
                <circle
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  stroke="#FFC107"
                  strokeWidth="16"
                  strokeLinecap="round"
                  strokeDasharray={`${(predictions.overall_placement_probability / 100) * 503.36} ${503.36}`}
                  transform="rotate(-90 100 100)"
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div>
                  <div className="text-6xl mb-2" style={{ fontWeight: 700 }}>{predictions.overall_placement_probability}%</div>
                  <div className="text-sm text-white/80">
                    {predictions.overall_placement_probability >= 80 ? "High Probability" :
                     predictions.overall_placement_probability >= 60 ? "Good Probability" :
                     predictions.overall_placement_probability >= 40 ? "Moderate Probability" : "Low Probability"}
                  </div>
                </div>
              </div>
            </div>

            <p className="text-lg text-white/90 max-w-2xl mx-auto">
              Based on your technical skills, academic performance, and overall profile analysis, 
              this is your estimated chance of securing a placement.
            </p>
          </Card>
        </motion.div>

        {isLowProbabilityCase ? (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            <div className="mb-2">
              <h2 className="text-3xl mb-2" style={{ fontWeight: 700 }}>Low Probability Analysis Report</h2>
              <p className="text-muted-foreground">This report is generated from your actual model input values and highlights practical changes to improve your prediction.</p>
            </div>

            <Card className="p-6 border-[#D97706]/30 bg-gradient-to-br from-[#D97706]/10 to-[#F59E0B]/10">
              <h3 className="text-xl font-bold mb-2">Why Your Probability Is Low</h3>
              <p className="text-sm text-muted-foreground mb-4">{lowReport?.summary || "Your current profile has high-impact gaps in core placement parameters."}</p>
              <div className="space-y-3">
                {(lowReport?.reasons || []).map((reason, index) => (
                  <div key={`${reason.parameter}-${index}`} className="rounded-lg border border-border/70 bg-background/70 p-4">
                    <div className="flex items-center justify-between gap-3 mb-1">
                      <p className="font-semibold">{reason.parameter}</p>
                      <span className="text-xs px-2 py-1 rounded-full bg-destructive/10 text-destructive border border-destructive/20">Impact: {reason.impact}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{reason.why_it_matters}</p>
                    <p className="text-sm mt-2">
                      Current: <span className="font-medium">{reason.current}</span> | Target: <span className="font-medium">{reason.target}</span> | Gap: <span className="font-medium">{reason.gap}</span>
                    </p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6 border-[#003366]/20 bg-gradient-to-br from-[#003366]/5 to-[#0055A4]/5">
              <h3 className="text-xl font-bold mb-4">Practical Changes You Should Do</h3>
              <div className="space-y-3">
                {(lowReport?.practical_changes || []).map((change, index) => (
                  <div key={`${change.focus_area}-${index}`} className="rounded-lg border border-border/70 bg-background/80 p-4">
                    <p className="font-semibold mb-1">{change.focus_area}</p>
                    <p className="text-sm mb-2">{change.action}</p>
                    <p className="text-xs text-muted-foreground">Target: {change.target} | Timeline: {change.timeline}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6 border-[#6366F1]/30 bg-gradient-to-br from-[#6366F1]/10 to-[#4F46E5]/10">
              <h3 className="text-xl font-bold mb-3">Peer Comparison</h3>
              <p className="text-sm mb-3">
                {lowReport?.peer_comparison?.bottom_bucket_statement || lowReport?.peer_comparison?.message || "Peer comparison data is not available right now."}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="rounded-md border border-border/60 bg-background/80 p-3">
                  <p className="text-xs text-muted-foreground">Top 25% DSA</p>
                  <p className="font-semibold">{lowReport?.peer_comparison?.top_25_percent_thresholds?.dsa_score_q75 ?? "N/A"}</p>
                </div>
                <div className="rounded-md border border-border/60 bg-background/80 p-3">
                  <p className="text-xs text-muted-foreground">Top 25% Projects</p>
                  <p className="font-semibold">{lowReport?.peer_comparison?.top_25_percent_thresholds?.project_score_q75 ?? "N/A"}</p>
                </div>
                <div className="rounded-md border border-border/60 bg-background/80 p-3">
                  <p className="text-xs text-muted-foreground">Top 25% Technical</p>
                  <p className="font-semibold">{lowReport?.peer_comparison?.top_25_percent_thresholds?.technical_score_q75 ?? "N/A"}</p>
                </div>
              </div>
            </Card>

            <Card className="p-6 border-[#0EA5E9]/30 bg-gradient-to-br from-[#0EA5E9]/10 to-[#0284C7]/10">
              <h3 className="text-xl font-bold mb-3">Confidence / Reliability</h3>
              <p className="text-sm mb-1">
                Prediction Confidence: <span className="font-semibold">{lowReport?.confidence_reliability?.confidence_label || "Unknown"}</span>
                {typeof lowReport?.confidence_reliability?.uncertainty_pct === "number" ? ` (±${lowReport.confidence_reliability.uncertainty_pct}%)` : ""}
              </p>
              <p className="text-sm text-muted-foreground">Reason: {lowReport?.confidence_reliability?.reason || "Insufficient reliability signals."}</p>
            </Card>

            <Card className="p-6 border-[#EF4444]/30 bg-gradient-to-br from-[#EF4444]/10 to-[#DC2626]/10">
              <h3 className="text-xl font-bold mb-3">Risk Alerts</h3>
              {(lowReport?.risk_alerts || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No critical risk alerts were generated.</p>
              ) : (
                <div className="space-y-2">
                  {(lowReport?.risk_alerts || []).map((alert, idx) => (
                    <div key={`${alert.title}-${idx}`} className="rounded-md border border-[#EF4444]/30 bg-white/70 p-3">
                      <p className="text-sm font-semibold">[{alert.severity}] {alert.title}</p>
                      <p className="text-sm text-muted-foreground">{alert.risk}</p>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card className="p-6 border-[#8B5CF6]/30 bg-gradient-to-br from-[#8B5CF6]/10 to-[#7C3AED]/10">
              <h3 className="text-xl font-bold mb-3">Projected Improvement Impact</h3>
              {lowReport?.projected_improvement?.placement_probability && lowReport?.projected_improvement?.predicted_salary_lpa ? (
                <div className="space-y-2 text-sm">
                  <p>
                    Placement Probability: <span className="font-semibold">{lowReport.projected_improvement.placement_probability.current}%</span> {"->"} <span className="font-semibold">{lowReport.projected_improvement.placement_probability.projected}%</span>
                    {" "}(Delta: {lowReport.projected_improvement.placement_probability.delta}%)
                  </p>
                  <p>
                    Expected Salary: <span className="font-semibold">{lowReport.projected_improvement.predicted_salary_lpa.current} LPA</span> {"->"} <span className="font-semibold">{lowReport.projected_improvement.predicted_salary_lpa.projected} LPA</span>
                    {" "}(Delta: {lowReport.projected_improvement.predicted_salary_lpa.delta} LPA)
                  </p>
                  <p className="text-xs text-muted-foreground">{lowReport?.projected_improvement?.simulation_note || "Scenario-based estimate."}</p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Projected improvement impact is currently unavailable.</p>
              )}
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-bold mb-4">Data Used For This Analysis</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(lowReport?.data_snapshot || {}).map(([key, value]) => (
                  <div key={key} className="rounded-md border border-border/70 px-3 py-2 bg-muted/30">
                    <p className="text-xs text-muted-foreground">{key.replace(/_/g, " ")}</p>
                    <p className="text-sm font-semibold">{String(value)}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6 border-[#10B981]/30 bg-gradient-to-br from-[#10B981]/10 to-[#059669]/10">
              <h3 className="text-xl font-bold mb-2">How To Improve Your Prediction</h3>
              <p className="text-sm">{lowReport?.final_note || "If you implement all the above, your prediction can improve."}</p>
            </Card>
          </motion.section>
        ) : (
          <>
            {/* Salary Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <div className="mb-6">
                <h2 className="text-3xl mb-2" style={{ fontWeight: 700 }}>💰 Salary Prediction</h2>
                <p className="text-muted-foreground">Expected salary and salary probability thresholds</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Card className="p-6 bg-gradient-to-br from-[#003366]/10 to-[#0055A4]/10 border-[#003366]/20">
                  <p className="text-sm text-muted-foreground mb-2">Predicted Salary</p>
                  <p className="text-4xl font-bold text-[#003366]">₹{predictions.predicted_salary_lpa} LPA</p>
                </Card>

                <Card className="p-6 bg-gradient-to-br from-[#10B981]/10 to-[#059669]/10 border-[#10B981]/20">
                  <p className="text-sm text-muted-foreground mb-2">Salary Range</p>
                  <p className="text-lg font-bold text-[#10B981]">
                    ₹{predictions.salary_range_min_lpa} - ₹{predictions.salary_range_max_lpa} LPA
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">Min to Max Range</p>
                </Card>

                <Card className="p-6 bg-gradient-to-br from-[#FFC107]/10 to-[#F59E0B]/10 border-[#FFC107]/20">
                  <p className="text-sm text-muted-foreground mb-2">Mid Range</p>
                  <p className="text-2xl font-bold text-[#FFC107]">₹{predictions.salary_range_mid_lpa} LPA</p>
                </Card>
              </div>

              {/* Salary Thresholds */}
              <Card className="p-6">
                <button 
                  onClick={() => setExpandedSalaries(!expandedSalaries)}
                  className="w-full flex items-center justify-between mb-4 hover:opacity-80 transition-opacity"
                >
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    <BarChart2 className="w-5 h-5" />
                    Cumulative Salary Probabilities
                  </h3>
                  {expandedSalaries ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>

                {expandedSalaries && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-4"
                  >
                    {salaryThresholds.map((threshold, index) => (
                      <motion.div
                        key={threshold.label}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{threshold.label}</span>
                          <span className="text-sm font-bold text-[#003366]">{threshold.value}%</span>
                        </div>
                        <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${threshold.value}%` }}
                            transition={{ delay: index * 0.1 + 0.2, duration: 0.8 }}
                            className="h-full bg-gradient-to-r from-[#003366] to-[#0055A4]"
                          />
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </Card>
            </motion.section>

            {/* Job Role Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <div className="mb-6">
                <h2 className="text-3xl mb-2" style={{ fontWeight: 700 }}>🎯 Predicted Job Role</h2>
              </div>

              <Card className="p-8 bg-gradient-to-br from-[#FFC107]/10 to-[#F59E0B]/10 border-[#FFC107]/20 text-center">
                <div className="text-6xl mb-4">💼</div>
                <h3 className="text-3xl font-bold text-[#FFC107] mb-2">{predictions.predicted_job_role}</h3>
                <p className="text-muted-foreground">Based on your skills and profile</p>
              </Card>
            </motion.section>

            {/* Recommended Companies Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <div className="mb-6">
                <h2 className="text-3xl mb-2" style={{ fontWeight: 700 }}>🏢 Recommended Companies</h2>
                <p className="text-muted-foreground">Best-fit companies based on your profile</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {companies.map((company, index) => (
                  <motion.div
                    key={company}
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="p-6 hover:shadow-lg transition-shadow border-[#003366]/20 bg-gradient-to-br from-[#003366]/5 to-[#0055A4]/5">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-[#003366] to-[#0055A4] rounded-lg flex items-center justify-center text-white text-xs font-bold">
                          {company.charAt(0)}
                        </div>
                        <h3 className="font-bold text-lg">{company}</h3>
                      </div>
                      <p className="text-sm text-muted-foreground">Recommended match</p>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </motion.section>
          </>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex gap-4 pt-8 pb-12"
        >
          <Link to="/placement-probability" className="flex-1">
            <Button className="w-full h-12 bg-gradient-to-r from-[#003366] to-[#0055A4] hover:opacity-90">
              <TrendingUp className="w-4 h-4 mr-2" />
              Generate New Prediction
            </Button>
          </Link>
          <Button variant="outline" className="h-12 px-6" onClick={downloadPredictionReport}>
            <Download className="w-4 h-4 mr-2" />
            Download Report
          </Button>
        </motion.div>
      </main>
    </div>
  );
}
