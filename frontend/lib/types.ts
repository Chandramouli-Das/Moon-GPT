export type Role = "user" | "assistant";

export type Message = {
  id: string;
  role: Role;
  content: string;
  action?: ChatAction | null;
};

export type ChatAction = {
  type: "resume_download" | "email_draft" | "email_sent";
  label: string;
};

export type Profile = {
  name: string;
  title: string;
  location: string;
  availability: string;
  summary: string;
  highlights: { value: string; label: string }[];
  skills: string[];
  links: {
    linkedin: string;
    github: string;
    appointment: string;
  };
};
