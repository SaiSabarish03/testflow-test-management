import * as path from 'path';

export const STORAGE_STATE = {
  admin: path.resolve(__dirname, '../.auth/admin.json'),
  qa: path.resolve(__dirname, '../.auth/qa.json'),
  viewer: path.resolve(__dirname, '../.auth/viewer.json'),
};
