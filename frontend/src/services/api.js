const NEARBY_HOTELS_PATH = '/api/hotels/nearby'
const SAVED_HOTELS_PATH = '/api/saved-hotels'
const HOTEL_RECOMMENDATIONS_PATH = '/api/hotels/recommended'
const USERS_PATH = '/api/users'
const BOOKINGS_PATH = '/api/bookings'
const AUTH_PATH = '/api/auth'
const SEARCH_HISTORY_PATH = '/api/search-history'
const CHAT_PATH = '/api/chat'

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

function validateNearbyCollection(data) {
  validateCollection(data, 'The live hotel search service')
  if (
    !data.center ||
    typeof data.center.postcode !== 'string' ||
    !Number.isFinite(data.center.latitude) ||
    !Number.isFinite(data.center.longitude) ||
    !['postcode boundary', 'expanded radius'].includes(data.search_scope) ||
    typeof data.hotel_source !== 'string' ||
    typeof data.postcode_source !== 'string' ||
    (data.search_scope === 'expanded radius' && !Number.isInteger(data.search_radius_miles))
  ) {
    throw new ApiRequestError('The live hotel search service returned an unexpected response.')
  }
  return data
}

function validateSavedHotelCollection(data) {
  validateCollection(data, 'The local hotel service')
  if (
    !Array.isArray(data.saved_hotel_ids) ||
    data.result_source !== 'Saved locally' ||
    data.complete_area_inventory !== false ||
    (data.count > 0 &&
      (!data.center ||
        !Number.isFinite(data.center.latitude) ||
        !Number.isFinite(data.center.longitude)))
  ) {
    throw new ApiRequestError('The local hotel service returned an unexpected response.')
  }
  return data
}

export async function searchNearbyHotels(postcode, token = '', limit = 20) {
  const parameters = new URLSearchParams({ postcode, limit: String(limit) })
  return validateNearbyCollection(
    await requestJson(
      `${NEARBY_HOTELS_PATH}?${parameters.toString()}`,
      token ? { headers: { Authorization: `Bearer ${token}` } } : {},
      'The live hotel search service',
    ),
  )
}

export async function getSavedHotels(postcode) {
  const parameters = new URLSearchParams({ postcode })
  return validateSavedHotelCollection(
    await requestJson(
      `${SAVED_HOTELS_PATH}?${parameters.toString()}`,
      {},
      'The local hotel service',
    ),
  )
}

export function saveHotelLocally(payload) {
  return requestJson(
    SAVED_HOTELS_PATH,
    { method: 'POST', body: JSON.stringify(payload) },
    'The local hotel service',
  )
}

export function removeSavedHotel(placeId) {
  return requestJson(
    `${SAVED_HOTELS_PATH}/${encodeURIComponent(placeId)}`,
    { method: 'DELETE' },
    'The local hotel service',
  )
}

export function registerAccount(payload) {
  return requestJson(
    `${AUTH_PATH}/register`,
    { method: 'POST', body: JSON.stringify(payload) },
    'The account service',
  )
}

export function loginAccount(payload) {
  return requestJson(
    `${AUTH_PATH}/login`,
    { method: 'POST', body: JSON.stringify(payload) },
    'The account service',
  )
}

export function logoutAccount(token) {
  return requestJson(
    `${AUTH_PATH}/logout`,
    {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
    'The account service',
  )
}

export function getCurrentAccount(token) {
  return requestJson(
    `${AUTH_PATH}/me`,
    { headers: { Authorization: `Bearer ${token}` } },
    'The account service',
  )
}

export async function getSearchHistory(token) {
  const data = await requestJson(
    SEARCH_HISTORY_PATH,
    { headers: { Authorization: `Bearer ${token}` } },
    'The search history service',
  )
  if (!Array.isArray(data)) {
    throw new ApiRequestError('The search history service returned an unexpected response.')
  }
  return data
}

export async function sendChatMessage(message, history = []) {
  const data = await requestJson(
    CHAT_PATH,
    {
      method: 'POST',
      body: JSON.stringify({ message, history }),
    },
    'The support chatbot',
  )
  if (!data || typeof data.reply !== 'string' || typeof data.model !== 'string') {
    throw new ApiRequestError('The support chatbot returned an unexpected response.')
  }
  if (
    data.usage !== null &&
    data.usage !== undefined &&
    (!Number.isInteger(data.usage.prompt_tokens) ||
      !Number.isInteger(data.usage.response_tokens) ||
      !Number.isInteger(data.usage.total_tokens) ||
      data.usage.prompt_tokens < 0 ||
      data.usage.response_tokens < 0 ||
      data.usage.total_tokens < 0)
  ) {
    throw new ApiRequestError('The support chatbot returned unexpected usage data.')
  }
  return data
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
