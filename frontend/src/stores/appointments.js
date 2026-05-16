import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

// Extracts a user-friendly error message from an Axios error
function parseError(err, fallback) {
  if (!err.response) {
    return 'Network error — please check your connection and try again.'
  }
  const status = err.response.status
  if (status === 503) return 'The service is temporarily unavailable. Please try again in a few moments.'
  if (status === 504) return 'The service is taking too long to respond. Please try again.'
  if (status === 400) {
    const data = err.response.data
    if (typeof data === 'object' && !data.detail) {
      // Flatten validation errors into a readable string
      const messages = Object.entries(data).map(([f, v]) => `${f}: ${Array.isArray(v) ? v.join(', ') : v}`)
      return messages.join(' | ')
    }
    return data?.detail || fallback
  }
  return err.response?.data?.detail || fallback
}

export const useAppointmentsStore = defineStore('appointments', () => {
  const appointments = ref([])   // doctor: their appointments | patient: their bookings
  const doctors      = ref([])   // list of available doctors (for patient to pick)
  const loading      = ref(false)
  const error        = ref(null)

  // Fetch appointments for the logged-in user (role-aware on the backend)
  async function fetchAppointments() {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.get('/appointments/')
      appointments.value = data
    } catch {
      error.value = 'Could not load appointments.'
    } finally {
      loading.value = false
    }
  }

  // Fetch list of doctors (used by patient when booking)
  async function fetchDoctors() {
    try {
      const { data } = await api.get('/auth/doctors/')
      doctors.value = data
    } catch (err) {
      doctors.value = []
      error.value = parseError(err, 'Could not load the list of doctors.')
    }
  }

  // Patient books an appointment with a doctor
  async function bookAppointment({ doctor_id, date, time, prediction_id }) {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.post('/appointments/', { doctor_id, date, time, prediction_id })
      appointments.value.unshift(data)
      return data
    } catch (err) {
      error.value = parseError(err, 'Booking failed. Please try again.')
      throw err
    } finally {
      loading.value = false
    }
  }

  // Doctor confirms or cancels an appointment; patient can only cancel
  async function updateAppointmentStatus(appointmentId, newStatus) {
    loading.value = true
    error.value   = null
    try {
      const { data } = await api.patch(`/appointments/${appointmentId}/status/`, { status: newStatus })
      const idx = appointments.value.findIndex((a) => a.id === appointmentId)
      if (idx !== -1) appointments.value[idx] = data
      return data
    } catch (err) {
      error.value = parseError(err, 'Could not update appointment status.')
      throw err
    } finally {
      loading.value = false
    }
  }

  return { appointments, doctors, loading, error, fetchAppointments, fetchDoctors, bookAppointment, updateAppointmentStatus }
})
