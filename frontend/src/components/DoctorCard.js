"use client";

import { MapPin, Stethoscope, ExternalLink } from "lucide-react";

const DoctorCard = ({
  name,
  providerType,
  address,
  city,
  state,
  email, // use email instead of fee
}) => {
  const cleanName = name || "Therapist Unknown";

  // Combine address, city, state
  const location = address
    ? `${address}${city ? ", " + city : ""}${state ? ", " + state : ""}`
    : "Location not specified";

  // Google Maps search link
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    location
  )}`;

  return (
    <div className="doctor-card card-hover">
      {/* Icon */}
      <div className="doctor-icon-container">
        <Stethoscope size={28} className="text-white" />
      </div>

      {/* Therapist Info */}
      <div className="doctor-info">
        <h3 className="doctor-name">{cleanName}</h3>
        <p className="doctor-speciality">{providerType || "Therapist"}</p>
        {email && <p className="doctor-email">Email: {email}</p>}
        <a
          href={mapsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="doctor-location group"
        >
          <MapPin size={16} className="doctor-location-icon" />
          <span className="doctor-location-text">{location}</span>
          <ExternalLink size={14} className="doctor-location-external" />
        </a>
      </div>
    </div>
  );
};

export default DoctorCard;
