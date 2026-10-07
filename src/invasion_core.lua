-- Engine-independent logic. No cm/core globals and no invented database keys.
-- The game adapter and persisted operation reconciliation are not implemented.
local M = {}

local function integer(value, minimum)
    return type(value) == "number" and value == math.floor(value)
        and value < math.huge and value >= minimum
end

function M.new_state(config)
    return {version = 1, requisition = config.systems.requisition.initial,
        arrived = false, rewarded = {}, pending = {}, completed = {}, portal_pending = false}
end

-- Caller supplies candidates obtained from the actual campaign map and checked
-- for land, ownership, visibility and start-position compatibility.
-- No assumption is made that every region on Immortal Empires is eligible.
function M.choose_portal(candidates, resolve, random_index)
    local valid, seen = {}, {}
    for _, candidate in ipairs(candidates) do
        assert(type(candidate.key) == "string" and candidate.key ~= "", "Invalid region key")
        if candidate.eligible and not seen[candidate.key] then
            seen[candidate.key] = true
            local x, y = resolve(candidate.key)
            if integer(x, 0) and integer(y, 0) then
                valid[#valid + 1] = {key = candidate.key, x = x, y = y}
            end
        end
    end
    table.sort(valid, function(a, b) return a.key < b.key end)
    if #valid == 0 then return nil, "no_valid_region" end
    local index = random_index(#valid)
    assert(integer(index, 1) and index <= #valid, "Invalid RNG index")
    return valid[index]
end

function M.begin_arrival(state, location)
    if state.arrived then return false, "already_arrived" end
    if state.portal_pending then return false, "pending_arrival" end
    if not location then return false, "no_valid_region" end
    assert(type(location.key) == "string" and location.key ~= ""
        and integer(location.x, 0) and integer(location.y, 0), "Invalid arrival location")
    state.portal_pending = {key = location.key, x = location.x, y = location.y}
    return true
end

function M.finish_arrival(state, succeeded)
    assert(type(succeeded) == "boolean", "Spawn result must be explicit")
    if not state.portal_pending then return false, "no_pending_arrival" end
    if succeeded then
        state.arrived = true
        state.arrival_region = state.portal_pending.key
        state.objective_region = state.portal_pending.key
    end
    state.portal_pending = false
    return succeeded
end

-- Stable engine event IDs must be provided by the future adapter. Rewards are
-- deduplicated across calls/reloads; no generic BattleCompleted assumption.
function M.reward(state, config, event_id, kind)
    assert(type(event_id) == "string" and event_id ~= "", "Missing event ID")
    local system = config.systems.requisition
    local amount
    if kind == "turn" then amount = system.turn_income
    elseif kind == "victory" then amount = system.victory_income
    else error("Unknown reward kind") end
    local key = kind .. ":" .. event_id
    if state.rewarded[key] then return false, "already_rewarded" end
    state.rewarded[key] = true
    local reserved = 0
    for _, request in pairs(state.pending) do reserved = reserved + request.cost end
    state.requisition = math.min(system.cap - reserved, state.requisition + amount)
    return true
end

function M.reserve_reinforcement(state, config, request_id, unit_id, army_id, army_size)
    assert(type(request_id) == "string" and request_id ~= "", "Missing request ID")
    assert(integer(army_size, 0), "Invalid army size")
    assert(type(army_id) == "string" and army_id ~= "", "Missing army ID")
    if state.pending[request_id] or state.completed[request_id] then return false, "duplicate_request" end
    local unit = config.units[unit_id]
    if not unit then return false, "unknown_unit" end
    -- Only one unacknowledged engine grant per army. The next request must
    -- re-read actual army size after confirming the previous grant.
    for _, request in pairs(state.pending) do
        if request.army_id == army_id then return false, "army_operation_pending" end
    end
    if army_size >= config.systems.requisition.army_capacity then return false, "army_full" end
    if state.requisition < unit.cost then return false, "insufficient_requisition" end
    -- Reserve funds before calling the game; unsuccessful operations refund.
    state.requisition = state.requisition - unit.cost
    state.pending[request_id] = {unit_id = unit_id, cost = unit.cost, army_id = army_id}
    return true
end

function M.finish_reinforcement(state, config, request_id, succeeded)
    assert(type(succeeded) == "boolean", "Grant result must be explicit")
    local request = state.pending[request_id]
    if not request then return false, "no_pending_request" end
    if not succeeded then
        state.requisition = math.min(config.systems.requisition.cap, state.requisition + request.cost)
    end
    state.pending[request_id] = nil
    state.completed[request_id] = succeeded and "granted" or "failed"
    return true
end

function M.settlement_captured(state, region_key)
    if state.arrived and region_key == state.objective_region then
        state.objective_completed = true
        return true
    end
    return false
end

return M
