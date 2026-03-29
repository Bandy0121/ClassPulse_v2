import { get } from './index.js'

export const fetchStudentStatistics = () => get('stats/student/statistics')
export const fetchClassStatistics = (classId) => get(`stats/teacher/class/${classId}/statistics`)
