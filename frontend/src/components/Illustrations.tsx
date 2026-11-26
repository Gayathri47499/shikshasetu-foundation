import React from "react";
import { motion } from "framer-motion";

/**
 * Cohesive set of original cartoon-style school & education SVG illustrations
 * in the ShikshaSetu Foundation baby-pink, rose, pastel-green & charcoal palette.
 */

export const SchoolHeroIllustration: React.FC<{ className?: string }> = ({ className = "w-full max-w-md" }) => (
  <svg viewBox="0 0 420 300" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
    {/* Soft blush sky blob */}
    <ellipse cx="210" cy="165" rx="185" ry="110" fill="#FFF1F5" />
    {/* Floating decorative book & graduation cap */}
    <motion.g
      animate={{ y: [0, -6, 0] }}
      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
    >
      <rect x="42" y="54" width="46" height="34" rx="6" fill="#FFFFFF" stroke="#F6C9D5" strokeWidth="2.5" />
      <path d="M52 65H78M52 74H70" stroke="#D97998" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="358" cy="64" r="22" fill="#E8F5EC" stroke="#4D9B78" strokeWidth="2" />
      <path d="M344 64L358 56L372 64L358 72L344 64Z" fill="#4D9B78" />
      <path d="M350 68V75C350 75 358 79 366 75V68" stroke="#4D9B78" strokeWidth="2" strokeLinecap="round" />
    </motion.g>

    {/* School Building */}
    <rect x="115" y="102" width="190" height="130" rx="12" fill="#FFFFFF" stroke="#D97998" strokeWidth="3" />
    {/* Roof */}
    <path d="M100 108L210 46L320 108H100Z" fill="#F6C9D5" stroke="#D97998" strokeWidth="3" strokeLinejoin="round" />
    {/* School Clock / Emblem */}
    <circle cx="210" cy="84" r="14" fill="#FFFFFF" stroke="#D97998" strokeWidth="2.5" />
    <path d="M210 77V84L215 87" stroke="#28313B" strokeWidth="2.2" strokeLinecap="round" />
    {/* Windows */}
    <rect x="135" y="124" width="32" height="30" rx="5" fill="#FFF1F5" stroke="#D97998" strokeWidth="2" />
    <rect x="253" y="124" width="32" height="30" rx="5" fill="#FFF1F5" stroke="#D97998" strokeWidth="2" />
    {/* Door */}
    <rect x="188" y="166" width="44" height="66" rx="8" fill="#F6C9D5" stroke="#D97998" strokeWidth="2.5" />
    <circle cx="222" cy="200" r="3" fill="#28313B" />

    {/* Ground */}
    <rect x="55" y="232" width="310" height="12" rx="6" fill="#E8F5EC" />

    {/* Cartoon Students studying with books (Left & Right) */}
    {/* Student 1 */}
    <circle cx="90" cy="182" r="16" fill="#FDE0D2" stroke="#28313B" strokeWidth="2.2" />
    <path d="M75 178C77 166 103 166 105 178" fill="#28313B" />
    <circle cx="85" cy="183" r="1.8" fill="#28313B" />
    <circle cx="95" cy="183" r="1.8" fill="#28313B" />
    <path d="M86 189C88 192 92 192 94 189" stroke="#D97998" strokeWidth="2" strokeLinecap="round" />
    <rect x="74" y="199" width="32" height="33" rx="10" fill="#D97998" />
    {/* Backpack */}
    <rect x="64" y="203" width="12" height="22" rx="5" fill="#4D9B78" />
    {/* Book in hand */}
    <rect x="96" y="205" width="18" height="14" rx="3" fill="#FFFFFF" stroke="#28313B" strokeWidth="1.8" />

    {/* Student 2 & Teacher / Outreach Worker */}
    <circle cx="328" cy="180" r="17" fill="#FDE0D2" stroke="#28313B" strokeWidth="2.2" />
    <path d="M312 176C314 163 342 163 344 176" fill="#28313B" />
    <circle cx="322" cy="181" r="1.8" fill="#28313B" />
    <circle cx="334" cy="181" r="1.8" fill="#28313B" />
    <path d="M324 188C327 191 331 191 334 188" stroke="#D97998" strokeWidth="2" strokeLinecap="round" />
    <rect x="310" y="198" width="36" height="34" rx="11" fill="#4D9B78" />
    {/* Pencil */}
    <path d="M294 212L312 198L316 203L298 217L294 212Z" fill="#F6C9D5" stroke="#28313B" strokeWidth="1.5" />
  </svg>
);

export const TeacherHelpingIllustration: React.FC<{ className?: string }> = ({ className = "w-32 h-24" }) => (
  <svg viewBox="0 0 180 130" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
    <rect x="10" y="14" width="160" height="102" rx="16" fill="#FFF1F5" />
    {/* Blackboard */}
    <rect x="30" y="24" width="78" height="44" rx="6" fill="#28313B" stroke="#F6C9D5" strokeWidth="2.5" />
    <path d="M42 40H92M42 52H76" stroke="#E8F5EC" strokeWidth="2.5" strokeLinecap="round" />
    {/* Teacher */}
    <circle cx="126" cy="52" r="14" fill="#FDE0D2" stroke="#28313B" strokeWidth="2" />
    <rect x="112" y="68" width="28" height="36" rx="9" fill="#D97998" />
    {/* Student */}
    <circle cx="66" cy="76" r="12" fill="#FDE0D2" stroke="#28313B" strokeWidth="2" />
    <rect x="54" y="89" width="24" height="22" rx="8" fill="#4D9B78" />
    <rect x="76" y="88" width="20" height="14" rx="3" fill="#FFFFFF" stroke="#D97998" strokeWidth="1.8" />
  </svg>
);

export const CommunityOutreachIllustration: React.FC<{ className?: string }> = ({ className = "w-32 h-24" }) => (
  <svg viewBox="0 0 180 130" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
    <rect x="10" y="14" width="160" height="102" rx="16" fill="#E8F5EC" />
    {/* Home */}
    <path d="M28 66L58 42L88 66V102H28V66Z" fill="#FFFFFF" stroke="#4D9B78" strokeWidth="2.2" strokeLinejoin="round" />
    <rect x="50" y="76" width="16" height="26" rx="3" fill="#F6C9D5" />
    {/* Outreach Worker with clipboard */}
    <circle cx="122" cy="54" r="13" fill="#FDE0D2" stroke="#28313B" strokeWidth="2" />
    <rect x="108" y="69" width="28" height="33" rx="9" fill="#D97998" />
    <rect x="94" y="73" width="14" height="18" rx="3" fill="#FFFFFF" stroke="#28313B" strokeWidth="1.6" />
    <path d="M98 79H104M98 84H104" stroke="#4D9B78" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

export const EmptyStateBooksIllustration: React.FC<{ className?: string }> = ({ className = "w-32 h-28" }) => (
  <svg viewBox="0 0 160 130" fill="none" xmlns="http://www.w3.org/2000/svg" className={className} aria-hidden="true">
    <circle cx="80" cy="65" r="52" fill="#FFF1F5" />
    <rect x="44" y="76" width="72" height="16" rx="4" fill="#F6C9D5" stroke="#D97998" strokeWidth="2" />
    <rect x="50" y="58" width="60" height="16" rx="4" fill="#FFFFFF" stroke="#D97998" strokeWidth="2" />
    <rect x="56" y="40" width="48" height="16" rx="4" fill="#E8F5EC" stroke="#4D9B78" strokeWidth="2" />
    <circle cx="118" cy="36" r="8" fill="#F6C9D5" />
  </svg>
);
