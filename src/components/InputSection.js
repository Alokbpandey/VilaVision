import React, { useState } from "react";
import "./InputSection.css";

function InputSection() {
  const [idea, setIdea] = useState("");
  const [model, setModel] = useState("Llama 31 405B");
  const [isShadow, setIsShadow] = useState(false);

  const handleGenerate = () => {
    alert(`Generating app for: ${idea} with model ${model}`);
  };

  return (
    <div className="input-section">
      <h2>Turn your <span className="highlight">idea</span> into an app</h2>
      <input
        type="text"
        placeholder="Build me a calculator app..."
        value={idea}
        onChange={(e) => setIdea(e.target.value)}
        className="input"
      />
      <button onClick={handleGenerate} className="generate-button">➔</button>
      <div className="options">
        <select value={model} onChange={(e) => setModel(e.target.value)} className="model-select">
          <option value="Llama 31 405B">Llama 31 405B</option>
          <option value="Other Model">Other Model</option>
        </select>
        <label className="shadow-checkbox">
          <input
            type="checkbox"
            checked={isShadow}
            onChange={() => setIsShadow(!isShadow)}
          />
          Shadow UI
        </label>
      </div>
    </div>
  );
}

export default InputSection;
