import { supabase } from '../lib/supabase'

export interface UserProfile {
  id: string
  user_id: string
  role: 'student' | 'teacher' | 'admin'
  name: string
  school_name?: string
  created_at: string
  updated_at: string
}

export interface StudentProfile {
  id: string
  user_id: string
  grade?: string
  class_name?: string
  target_industry?: string
  target_company?: string
  target_position?: string
  club_activity?: string
  achievements?: Array<{ title: string; description: string; date: string }>
  certifications?: Array<{ name: string; date: string; score?: string }>
  strengths?: string[]
  weaknesses?: string[]
  notes?: string
}

export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  const { data, error } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error) throw error
  return data
}

export async function getStudentProfile(userId: string): Promise<StudentProfile | null> {
  const { data, error } = await supabase
    .from('student_profiles')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error && error.code !== 'PGRST116') throw error
  return data
}

export async function updateUserProfile(userId: string, updates: Partial<UserProfile>) {
  const { data, error } = await supabase
    .from('user_profiles')
    .update(updates)
    .eq('user_id', userId)
    .select()
    .single()

  if (error) throw error
  return data
}

export async function updateStudentProfile(userId: string, updates: Partial<StudentProfile>) {
  const { data, error } = await supabase
    .from('student_profiles')
    .upsert({ user_id: userId, ...updates })
    .select()
    .single()

  if (error) throw error
  return data
}
