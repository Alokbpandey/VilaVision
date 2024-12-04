import React, { useState } from "react";
import { ArrowRight, Globe, Copy, Download } from "lucide-react"; // Icons from lucide-react
import { FiUpload } from "react-icons/fi"; // Upload icon
import axios from "axios";
import "./App.css";

function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [model, setModel] = useState("vila");
  const [image, setImage] = useState(null);
  const [imageURL, setImageURL] = useState(""); // URL input for images or videos
  const [result, setResult] = useState(null);
  const [filePreviewURL, setFilePreviewURL] = useState(null); // Preview URL for file
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // Loading state
  const [chatHistory, setChatHistory] = useState([]); // Chat history state
  const [showHistory, setShowHistory] = useState(false); // Toggle for chat history

  

  // Handle input field changes
  const handleInputChange = (e) => {
    setSearchQuery(e.target.value);
  };

  // Handle URL changes
const handleURLChange = (e) => {
  setImageURL(e.target.value);
};

  // Handle image upload
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setImageURL(""); // Clear URL input when a file is uploaded
      setFilePreviewURL(URL.createObjectURL(file)); // Generate preview URL
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    try {
      // Validate inputs
      if (!image && !imageURL.trim()) {
        alert("Please upload an image or provide a URL.");
        return;
      }
      if (!searchQuery.trim()) {
        alert("Please enter a prompt.");
        return;
      }

      setError(null);
      setResult(null);
      setIsLoading(true);

      const formData = new FormData();
      if (image) {
        formData.append("file", image); // Add uploaded image
      } else if (imageURL.trim()) {
        formData.append("url", imageURL); // Add image/video URL
      }
      formData.append("prompt", searchQuery); // Add user prompt
      formData.append("model", model); // Add model information

      // Send the request to the backend
      const response = await axios.post("http://127.0.0.1:5000/api/process", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // Process the response
      setResult(response.data);
    } catch (err) {
      setError("An error occurred while processing your request.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file upload button click
  const handleUpload = () => {
    document.getElementById("image-upload").click();
  };

  // Copy result to clipboard
  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      alert("Result copied to clipboard!");
    }
  };

  // Download result as a file
  const handleDownload = () => {
    if (result && result.file_url) {
      const link = document.createElement("a");
      link.href = result.file_url;
      link.download = result.file_name || "result";
      link.click();
    }
  };

  // Render file preview
  const renderFilePreview = () => {
    if (!filePreviewURL && !imageURL.trim()) return null;

    if (filePreviewURL) {
      return <img src={filePreviewURL} alt="Preview" className="preview-image" />;
    } else if (imageURL.trim()) {
      return (
        <img src={imageURL} alt="Preview from URL" className="preview-image" />
      );
    }
    return null;
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <Globe size={24} />
          VilaVision
        </div>
        <a href="#" className="github-link">
          GitHub Repo
        </a>
      </header>

      {/* Main Content */}
      <main className="content">
        <div className="model-info">Powered by Nvidia Nim</div>
        <h1 className="main-title">
        Bring Your <span className="highlight">Vision</span>  to {" "}
          <span className="highlight">words</span>
        </h1>

        <div className="container mx-auto p-4">
          {/* Search bar for prompt input */}
          <div className="search-bar flex items-center gap-2 mb-4 relative">
            <input
              type="text"
              className="input-field flex-grow border rounded px-4 py-2 text-sm pr-12"
              value={searchQuery}
              onChange={handleInputChange}
              placeholder="Describe the scene, summarize a video, or more..."
            />

            {/* Upload Icon Button */}
            <button
              className="upload-button absolute left-3 cursor-pointer bg-green-500 hover:bg-green-600 text-white p-2 rounded"
              onClick={handleUpload}
            >
              <FiUpload size={20} />
            </button>

            {/* ArrowRight Icon Button */}
            <button
              className="send-button absolute right-3 cursor-pointer bg-green-500 hover:bg-green-600 text-white p-2 rounded"
              onClick={handleSubmit}
            >
              <ArrowRight size={20} />
            </button>
          </div>

          {/* File Upload Section */}
          <div className="upload-section flex items-center gap-2 mb-4">
            <input
              type="file"
              accept="image/*,video/*,audio/*"
              onChange={handleImageUpload}
              style={{ display: "none" }}
              id="image-upload"
            />
          </div>

{/* Display Input Preview */}
{(filePreviewURL || imageURL) && (
  <div className="preview-section">
    <div className="preview-container">
      <div className="preview-display">
        {renderFilePreview()}
      </div>
      <div className="preview-actions">
        <button className="copy-btn" onClick={handleCopy}>
          Copy to Clipboard
        </button>
        <button className="download-btn" onClick={handleDownload}>
          Download File
        </button>
      </div>
    </div>
  </div>
)}

        {/* Loading Spinner */}
{isLoading && (
  <div className="spinner flex flex-col items-center justify-center mt-6">
    {/* Spinner Animation */}
    <div className="w-12 h-12 border-4 border-t-4 border-gray-200 rounded-full animate-spin border-t-blue-500"></div>
    {/* Loading Text */}
    <p className="text-gray-300 mt-4 text-lg font-medium animate-pulse">
      Processing your request...
    </p>
  </div>
)}
{/* Display Results */}
{result && (
  <div className="result mt-6 flex justify-center">
    <div className="result-card bg-gray-900 shadow-lg rounded-lg max-w-3xl w-full overflow-hidden">
      <div className="p-6">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className="rounded-full bg-gray-800 p-3">
            <Globe size={24} className="text-green-400" />
          </div>

          {/* Result Content */}
          <div className="flex-1">
            <div className="whitespace-pre-wrap text-gray-200 text-lg leading-relaxed">
              {typeof result.vila_response.choices[0].message.content === 'string'
                ? result.vila_response.choices[0].message.content
                : JSON.stringify(result.vila_response.choices[0].message.content, null, 2)}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 mt-6">
              <button
                className="p-2 bg-gray-800 hover:bg-red-600 text-gray-400 hover:text-white rounded-full transition-colors"
                aria-label="Copy to clipboard"
                onClick={handleCopy}
              >
                <Copy size={20} />
              </button>
              <button
                className="p-2 bg-gray-800 hover:bg-red-600 text-gray-400 hover:text-white rounded-full transition-colors"
                aria-label="Dislike response"
              >
                <svg viewBox="0 0 24 24" className="w-5 h-5">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
              </button>
              <button
                className="p-2 bg-gray-800 hover:bg-red-600 text-gray-400 hover:text-white rounded-full transition-colors"
                aria-label="Regenerate response"
              >
                <svg viewBox="0 0 24 24" className="w-5 h-5">
                  <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
                </svg>
              </button>
            </div>
          </div>
        </div>  
      
        {/* Feedback section */}
        <div className="mt-8 flex items-center justify-center border-t border-gray-800 pt-4">
        <div className="text-sm text-white">
    Is this conversation helpful so far?
           </div>
          </div>
        </div>
      </div>
    </div>
)}
          {/* Error Display */}
          {error && (
            <div className="error bg-red-500 text-white rounded p-2 mt-4">{error}</div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
