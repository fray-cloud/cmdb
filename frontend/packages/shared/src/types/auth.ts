export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  status: string;
  roles: string[];
}

export interface SignupRequest {
  email: string;
  username: string;
  password: string;
}
