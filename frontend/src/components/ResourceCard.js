"use client";

import { BookOpen, ExternalLink } from "lucide-react";

const ResourceCard = ({ title, url, content }) => {
  const snippet =
    content?.length > 120 ? content.substring(0, 120) + "..." : content;

  return (
    <div className="resource-card card-hover">
      {/* Icon */}
      <div className="resource-icon-container">
        <BookOpen size={28} className="text-white" />
      </div>

      {/* Resource Info */}
      <div className="resource-info">
        <h3 className="resource-title">{title || "Untitled Resource"}</h3>
        <p className="resource-snippet">{snippet || "No description available"}</p>

        {url && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="resource-link group"
          >
            <span className="resource-link-text">Read More</span>
            <ExternalLink size={14} className="resource-link-external" />
          </a>
        )}
      </div>
    </div>
  );
};

export default ResourceCard;
