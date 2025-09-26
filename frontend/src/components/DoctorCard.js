"use client";

import { MapPin, Stethoscope, ExternalLink } from "lucide-react";
import Image from "next/image";
const DoctorCard = ({
  name,
  speciality,
  location,
  fee,
  latitude,
  longitude,
}) => {
  const cleanName =
    name?.replace(/^Dr\.\s*Dr\.\s*/, "Dr. ").replace(/^Dr\s*Dr\s*/, "Dr. ") ||
    "Dr. Unknown";

  // Link to Google Maps for directions
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    location || ""
  )}`;

  // OpenStreetMap static map (no API key required)
  const mapImgUrl =
    latitude && longitude
      ? `https://staticmap.openstreetmap.de/staticmap.php?center=${latitude},${longitude}&zoom=15&size=300x200&markers=${latitude},${longitude},red-pushpin`
      : null;

  return (
    <div className="doctor-card card-hover">
      {/* Icon */}
      <div className="doctor-icon-container">
        <Stethoscope size={28} className="text-white" />
      </div>

      {/* Doctor Info */}
      <div className="doctor-info">
        <h3 className="doctor-name">{cleanName}</h3>
        <p className="doctor-speciality">
          {speciality || "General Practitioner"}
        </p>
        {fee && fee !== "Contact for fee" && (
          <p className="doctor-fee">Fee: {fee}</p>
        )}
        <a
          href={mapsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="doctor-location group"
        >
          <MapPin size={16} className="doctor-location-icon" />
          <span className="doctor-location-text">
            {location || "Location not specified"}
          </span>
          <ExternalLink size={14} className="doctor-location-external" />
        </a>
      </div>

      {/* Mini Map */}
      {mapImgUrl && (
        <div className="doctor-map">
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="doctor-map-link"
          >
            <div className="doctor-map-container">
              <Image
                src={mapImgUrl}
                alt={`Map of ${cleanName}`}
                className="doctor-map-image"
                width={30} // Set an appropriate width
                height={30} // Set an appropriate height
                style={{ borderRadius: "8px", objectFit: "cover" }}
              />
            </div>
          </a>
        </div>
      )}
    </div>
  );
};

export default DoctorCard;
