"use client";

import Image from "next/image";
import {
  ArrowUpRight,
  CalendarDays,
  Download,
  Github,
  Linkedin,
  MapPin,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { Profile } from "@/lib/types";
import { API_URL } from "@/lib/api";

const fallback: Profile = {
  name: "Chandramouli Das",
  title: "Lead Data Scientist · GenAI & AI Leadership",
  location: "Bangalore, India",
  availability: "Open to strategic AI conversations",
  summary:
    "AI/ML leader building production-grade Generative AI, RAG, NLP, and intelligent automation systems.",
  highlights: [
    { value: "6+", label: "Years in AI & Data" },
    { value: "10+", label: "Team members led" },
    { value: "1K+", label: "Learners mentored" },
  ],
  skills: [
    "Generative AI",
    "Data Science",
    "AI Leadership",
    "Agentic AI",
    "RAG Systems",
    "AI Strategy",
  ],
  links: {
    linkedin: "https://www.linkedin.com/in/chandramouli-das-38a7921a5/",
    github: "https://github.com/Chandramouli-Das",
    appointment: "https://topmate.io/chandramouli_das",
  },
};

export function ProfilePanel({ profile }: { profile: Profile | null }) {
  const data = profile ?? fallback;

  return (
    <aside className="profile-panel">
      <div className="brand">
        <span className="brand-mark"><Sparkles size={17} /></span>
        <span>MoonGPT</span>
        <small>Portfolio intelligence</small>
      </div>

      <div className="identity-card">
        <section className="identity">
          <div className="avatar-wrap">
            <div className="avatar-ring" />
            <div className="avatar">
              <Image
                src="/chandramouli-profile.webp"
                alt="Chandramouli Das"
                width={152}
                height={152}
                priority
              />
            </div>
            <span className="online-dot" aria-label="Available" />
          </div>
          <p className="eyebrow">Portfolio assistant for</p>
          <h1>{data.name}</h1>
          <p className="role">{data.title}</p>
          <div className="location"><MapPin size={14} /> {data.location}</div>
        </section>

        <div className="availability">
          <span className="pulse" />
          {data.availability}
        </div>
      </div>

      <p className="profile-summary">{data.summary}</p>

      <div className="stats">
        {data.highlights.map((item) => (
          <div className="stat" key={item.label}>
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      <div className="skills">
        <p className="section-label">Core expertise</p>
        <div className="skill-list">
          {data.skills.map((skill) => <span key={skill}>{skill}</span>)}
        </div>
      </div>

      <div className="profile-actions">
        <a className="primary-link" href={`${API_URL}/api/resume`}>
          <Download size={17} /> Download résumé
        </a>
        <a href={data.links.appointment} target="_blank" rel="noreferrer">
          <CalendarDays size={17} /> Book a conversation <ArrowUpRight size={15} />
        </a>
      </div>

      <div className="social-links">
        <a href={data.links.linkedin} target="_blank" rel="noreferrer" aria-label="LinkedIn">
          <Linkedin size={18} />
        </a>
        <a href={data.links.github} target="_blank" rel="noreferrer" aria-label="GitHub">
          <Github size={18} />
        </a>
        <span><ShieldCheck size={12} /> Verified résumé context</span>
      </div>
    </aside>
  );
}
