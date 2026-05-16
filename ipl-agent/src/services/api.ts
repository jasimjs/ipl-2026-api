const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

export interface LiveScore {
  status: string;
  season: string;
  source: string;
  live_count: number;
  matches: Record<string, {
    status: string;
    team_1: string;
    score_1: string;
    team_2: string;
    score_2: string;
    status_text?: string;
  }>;
}

export interface PointsTable {
  status_code: number;
  season: string;
  points_table: Record<string, {
    Name: string;
    Played: number;
    Won: number;
    Loss: number;
    "No Result": number;
    "Net Run Rate": number;
    Points: number;
  }>;
}

export interface Squad {
  status_code: number;
  team: string;
  squad: Record<string, {
    Name: string;
    Nationality: string;
    Role: string;
    Style: string;
    Wicketkeeper: boolean;
    Overseas: boolean;
    Captaincy?: string;
  }>;
}

export const api = {
  async getLiveScore(): Promise<LiveScore> {
    const response = await fetch(`${BASE_URL}/ipl-2026-live-score-s2`);
    if (!response.ok) throw new Error('Failed to fetch live scores');
    return response.json();
  },

  async getPointsTable(): Promise<PointsTable> {
    const response = await fetch(`${BASE_URL}/ipl-points-table`);
    if (!response.ok) throw new Error('Failed to fetch points table');
    return response.json();
  },

  async getSquad(teamCode: string): Promise<Squad> {
    const response = await fetch(`${BASE_URL}/squad/${teamCode}`);
    if (!response.ok) throw new Error(`Failed to fetch squad for ${teamCode}`);
    return response.json();
  },

  async getSchedule() {
    const response = await fetch(`${BASE_URL}/ipl-schedule`);
    if (!response.ok) throw new Error('Failed to fetch schedule');
    return response.json();
  }
};
