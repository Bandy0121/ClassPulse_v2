import { get, post, put, del } from './index.js'

export const fetchClasses = () => get('teacher/classes')
export const createClass = (data) => post('teacher/classes', data)
export const fetchClassDetail = (classId) => get(`teacher/classes/${classId}`)
export const updateClass = (classId, data) => put(`teacher/classes/${classId}`, data)
export const deleteClass = (classId) => del(`teacher/classes/${classId}`)

export const fetchClassAssessments = (classId) => get(`teacher/classes/${classId}/assessments`)
export const createAssessment = (classId, data) => post(`teacher/classes/${classId}/assessments`, data)
export const addQuestion = (assessmentId, data) => post(`teacher/assessments/${assessmentId}/questions`, data)
export const publishAssessment = (assessmentId, publish) =>
  put(`teacher/assessments/${assessmentId}/publish`, { publish })
export const deleteAssessment = (assessmentId) => del(`teacher/assessments/${assessmentId}`)
export const fetchAssessmentStatistics = (assessmentId) => get(`teacher/assessments/${assessmentId}/statistics`)

export const fetchClassCheckins = (classId) => get(`teacher/classes/${classId}/checkins`)
