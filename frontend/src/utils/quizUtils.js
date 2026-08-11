/**
 * Shared utility to parse and normalize quiz answers.
 */

// Match "A)", "A.", "A-", or just "A" at the start
const OPTION_LETTER_REGEX = /^([A-D])[\)\.\-\s]/i;
const OPTION_LETTER_ONLY_REGEX = /^([A-D])$/i;

export const extractOptionLetter = (optionString) => {
  if (!optionString) return "";
  const s = optionString.trim();
  const match = s.match(OPTION_LETTER_REGEX) || s.match(OPTION_LETTER_ONLY_REGEX);
  return match ? match[1].toUpperCase() : "";
};
