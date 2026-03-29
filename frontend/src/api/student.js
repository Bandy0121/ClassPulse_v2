import { get, post, del } from './index.js'

export const fetchStudentClasses = () => get('student/classes')
export const joinClass = (classCode) => post('student/classes/join', { class_code: classCode })
export const leaveClass = (classId) => del(`student/classes/${classId}`)

export const fetchAssessments = () => get('student/assessments')
export const fetchAssessmentDetail = (assessmentId) => get(`student/assessments/${assessmentId}`)
export const submitAssessment = (assessmentId, answers) =>
  post(`student/assessments/${assessmentId}/submit`, { answers })
export const fetchAssessmentResult = (assessmentId) => get(`student/assessments/${assessmentId}/result`)

export const checkin = (payload) => post('student/checkin', payload)
export const fetchCheckinHistory = () => get('student/checkin/history')
export const fetchHistory = () => get('student/history')
