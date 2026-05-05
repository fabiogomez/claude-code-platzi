// Course types — matches GET /courses response
export interface Course {
  id: number;
  name: string;
  description: string;
  thumbnail: string;
  slug: string;
  average_rating?: number;
  ratings_count?: number;
}

// Class summary returned inside GET /courses/:slug
export interface Class {
  id: number;
  name: string;
  description: string;
  slug: string;
}

// Course Detail — matches GET /courses/:slug
export interface CourseDetail extends Course {
  teacher_id: number[];
  classes: Class[];
}

// Rating types
export interface Rating {
  id: number;
  course_id: number;
  user_identifier: string;
  score: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface RatingCreate {
  score: number;
  user_identifier: string;
  comment?: string;
}

export interface RatingStats {
  average_rating: number;
  ratings_count: number;
}

// Progress types
export interface Progress {
  progress: number; // seconds
  user_id: number;
}

// Quiz types
export interface QuizOption {
  id: number;
  answer: string;
  correct: boolean;
}

export interface Quiz {
  id: number;
  question: string;
  options: QuizOption[];
}

// Favorite types
export interface FavoriteToggle {
  course_id: number;
}