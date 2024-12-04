import React from "react";
import { FaGithub } from "react-icons/fa";
import "./Header.css";

function Header() {
  return (
    <header className="header">
      <h1>LlamaCoder</h1>
      <a href="https://github.com/your-repo" className="github-link">
        <FaGithub /> GitHub Repo
      </a>
    </header>
  );
}

export default Header;
