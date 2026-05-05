const STORAGE_KEY = "platziflix_user_id";

export const getUserId = (): string => {
  if (typeof window === "undefined") {
    return "";
  }

  const existingId = localStorage.getItem(STORAGE_KEY);
  if (existingId) {
    return existingId;
  }

  const newId = crypto.randomUUID();
  localStorage.setItem(STORAGE_KEY, newId);
  return newId;
};
