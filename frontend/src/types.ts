/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface User {
  id: string;
  username: string;
  createdAt: string;
}

export interface DimensionScores {
  accuracy: number;     // 准确性 (0-100)
  completeness: number; // 完整性 (0-100)
  logic: number;        // 逻辑性 (0-100)
  expression: number;   // 表达能力 (0-100)
}

export interface Evaluation {
  score: number;
  dimensions: DimensionScores;
  strengths: string[];
  improvements: string[];
  feedback: string;
}

export interface Question {
  id: string;
  interviewId: string;
  questionText: string;
  questionType: 'technical' | 'behavioral' | 'system_design';
  category: string;
  difficulty: number; // 1-10
  followUps?: string[];
  userAnswer?: string;
  evaluation?: Evaluation;
  followUpCount?: number;
}

export interface Interview {
  id: string;
  userId: string;
  targetCompany: string;
  targetPosition: string;
  techStack: string[];
  interviewMode: 'technical' | 'behavioral' | 'stress';
  status: 'created' | 'in_progress' | 'completed';
  overallScore?: number;
  createdAt: string;
  durationMinutes?: number;
  questions?: Question[];
}

export interface InterviewSummary {
  interviewId: string;
  overallScore: number;
  totalQuestions: number;
  answeredQuestions: number;
  durationMinutes: number;
  categoryScores: Record<string, number>;
  dimensionSummary: DimensionScores;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface ChallengeItem {
  id: number;
  text: string;
  priority?: 'high' | 'medium' | 'low';
}

export interface UserProfile {
  userId: string;
  username: string;
  totalInterviews: number;
  averageScore: number;
  radarData: { name: string; score: number; fullMark: number }[];
  categoryData: { category: string; score: number }[];
  trendData: { date: string; score: number; title: string }[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  challenges: ChallengeItem[];
  knowledgeGraph: {
    nodes: { id: string; label: string; group: 'core' | 'sub' | 'weak' }[];
    links: { source: string; target: string; label?: string }[];
  };
}
