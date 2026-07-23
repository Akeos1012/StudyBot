import React from "react";

const ScoreCard = ({ score, totalQuestions, onResetQuiz }) => {
  const pct = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;

  return (
    <div className="border-t border-[#2a2d34] p-6 bg-[#101115]">
      <div className="card-elevated p-8 text-center">
        <p className="text-xs uppercase tracking-widest text-gray-500">Quiz Complete</p>
        <h2 className="mt-3 text-4xl font-bold accent-text-gradient">{score} / {totalQuestions}</h2>
        <p className="mt-2 text-sm text-gray-500">{pct}% correct · recorded for this session</p>

        <div className="sb-score-track">
          <div className="sb-score-fill" style={{ width: `${pct}%` }} />
        </div>

        <button onClick={onResetQuiz} className="sb-generate-btn mt-7" style={{ width: "auto", padding: "10px 24px" }}>
          New Quiz
        </button>
      </div>
    </div>
  );
};

export default ScoreCard;