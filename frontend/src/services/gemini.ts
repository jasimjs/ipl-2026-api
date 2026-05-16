const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export const geminiAgent = {
  async generateCommentary(matchData: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/commentary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(matchData),
      });
      
      if (!response.ok) {
        throw new Error('Backend commentary failed');
      }

      const data = await response.json();
      return data.commentary;
    } catch (error: any) {
      console.error("AI Commentary Agent Error:", error);
      const team1 = matchData.team_1 || "Team 1";
      const team2 = matchData.team_2 || "Team 2";
      return `Agent update: ${team1} and ${team2} are locked in an intense battle!`;
    }
  },

  async getWinProbability(matchData: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/win-probability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(matchData),
      });
      return await response.json();
    } catch (error) {
      return { team_1_prob: 50, team_2_prob: 50 };
    }
  },

  async getStrategy(matchData: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/strategy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(matchData),
      });
      const data = await response.json();
      return data.strategy;
    } catch (error) {
      return "Hold your nerve and stick to the basics!";
    }
  },

  async getFanChallenge(matchData: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/fan-challenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(matchData),
      });
      return await response.json();
    } catch (error) {
      return { challenge: "Predict the next boundary!", options: ["Yes", "No"] };
    }
  },

  async getGamification(userData: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/gamification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });
      return await response.json();
    } catch (error) {
      return { xp: 100, level: 1, badge: "Match Starter" };
    }
  },

  async getSquadXI(matchData: any) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/squad-xi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(matchData),
      });
      return await response.json();
    } catch (error) {
      return ["Virat Kohli (C)", "MS Dhoni (WK)", "Ravindra Jadeja", "Rashid Khan"];
    }
  },

  async getTeamInsights(teamName: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/team-insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_name: teamName }),
      });
      return await response.json();
    } catch (error) {
      return { insights: "Team is preparing for the next big clash.", key_player: "Captain" };
    }
  }
};