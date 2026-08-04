// Temporary user context service
const USER_ID_KEY = 'sb_user_id';

export const userService = {
  getUserId() {
    // Return stored ID, or default for now
    return localStorage.getItem(USER_ID_KEY) || 'test_user';
  },
  
  setUserId(id) {
    localStorage.setItem(USER_ID_KEY, id);
  }
};
