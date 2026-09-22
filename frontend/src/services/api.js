const HOTEL_SEARCH_PATH = '/api/hotels/search'
const HOTEL_RECOMMENDATIONS_PATH = '/api/hotels/recommended'
const USERS_PATH = '/api/users'
const BOOKINGS_PATH = '/api/bookings'

export class ApiRequestError extends Error {
  constructor(message, status = null) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
  }
}

async function requestJson(path, options = {}, fallbackMessage = 'The service') {
  let response

  try {
    response = await fetch(path, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiRequestError(`${fallbackMessage} could not be reached.`)
  }

  if (!response.ok) {
    let detail = ''
    try {
      detail = (await response.json()).detail
    } catch {
      // Use the stable fallback below when the error response is not JSON.
    }
    throw new ApiRequestError(detail || `${fallbackMessage} returned an error.`, response.status)
  }

  if (response.status === 204) {
    return null
  }

  try {
    return await response.json()
  } catch {
    throw new ApiRequestError(`${fallbackMessage} returned an invalid response.`, response.status)
  }
}

function validateCollection(data, fallbackMessage) {
  if (!data || !Array.isArray(data.results) || !Number.isInteger(data.count)) {
    throw new ApiRequestError(`${fallbackMessage} returned an unexpected response.`)
  }
  return data
}

export async function searchHotels(location, { checkIn = '', checkOut = '' } = {}) {
  const parameters = new URLSearchParams({ name: location })
  if (checkIn) parameters.set('check_in', checkIn)
  if (checkOut) parameters.set('check_out', checkOut)

  return validateCollection(
    await requestJson(
      `${HOTEL_SEARCH_PATH}?${parameters.toString()}`,
      {},
      'The search service',
    ),
    'The search service',
  )
}

export async function getRecommendedHotels(limit = 3) {
  const parameters = new URLSearchParams({ limit: String(limit) })
  return validateCollection(
    await requestJson(
      `${HOTEL_RECOMMENDATIONS_PATH}?${parameters.toString()}`,
      {},
      'The recommendation service',
    ),
    'The recommendation service',
  )
}

export async function getDemoUsers() {
  const data = await requestJson(USERS_PATH, {}, 'The traveler service')
  if (!Array.isArray(data)) {
    throw new ApiRequestError('The traveler service returned an unexpected response.')
  }
  return data
}

export async function getBookingHistory(userId) {
  const parameters = new URLSearchParams({ user_id: userId })
  const data = await requestJson(
    `${BOOKINGS_PATH}?${parameters.toString()}`,
    {},
    'The booking history service',
  )
  if (!Array.isArray(data)) {
    throw new ApiRequestError('The booking history service returned an unexpected response.')
  }
  return data
}

export function createBooking(userId, tripId) {
  return requestJson(
    BOOKINGS_PATH,
    {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, trip_id: tripId }),
    },
    'The booking service',
  )
}

export function cancelBooking(bookingId) {
  return requestJson(
    `${BOOKINGS_PATH}/${encodeURIComponent(bookingId)}/cancel`,
    { method: 'PATCH' },
    'The booking service',
  )
}

export function deleteBooking(bookingId) {
  return requestJson(
    `${BOOKINGS_PATH}/${encodeURIComponent(bookingId)}`,
    { method: 'DELETE' },
    'The booking service',
  )
}
