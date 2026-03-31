import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, viewToFilter } from '../api'

export function useTasks(view, tag, location, explicitFilter, showClosed = false) {
  const filter = explicitFilter !== undefined ? explicitFilter : viewToFilter(view, tag, location)
  return useQuery({
    queryKey: ['tasks', filter, showClosed],
    queryFn:  () => api.tasks.list(filter, showClosed),
    refetchInterval: 3000,
  })
}

export function useTaskCount(filter) {
  const { data = [] } = useQuery({
    queryKey: ['tasks', filter],
    queryFn:  () => api.tasks.list(filter),
    refetchInterval: 3000,
  })
  return data.length
}

export function useTask(taskId) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn:  () => api.tasks.get(taskId),
    enabled:  !!taskId,
  })
}

export function useCounts() {
  return useQuery({
    queryKey: ['counts'],
    queryFn:  api.counts,
    refetchInterval: 3000,
  })
}

export function useTags() {
  return useQuery({
    queryKey: ['tags'],
    queryFn:  api.tags,
    refetchInterval: 10_000,
  })
}

export function useLocations() {
  return useQuery({
    queryKey: ['locations'],
    queryFn:  api.locations,
    refetchInterval: 10_000,
  })
}

export function useFilters() {
  return useQuery({
    queryKey: ['filters'],
    queryFn:  api.filters.list,
    staleTime: Infinity,
  })
}

// ── mutations ─────────────────────────────────────────────────────────────────

function useInvalidate(...keys) {
  const qc = useQueryClient()
  return () => keys.forEach(key => qc.invalidateQueries({ queryKey: [key] }))
}

export function useCreateTask() {
  const invalidate = useInvalidate('tasks', 'counts', 'tags', 'locations')
  return useMutation({
    mutationFn: (text) => api.tasks.create(text),
    onSuccess:  invalidate,
  })
}

export function useUpdateTask() {
  const qc = useQueryClient()
  const invalidate = useInvalidate('tasks', 'tags', 'locations')
  return useMutation({
    mutationFn: ({ id, text }) => api.tasks.update(id, text),
    onSuccess: (updated) => {
      invalidate()
      qc.setQueryData(['task', updated.id], updated)
    },
  })
}

export function useCloseTask() {
  const invalidate = useInvalidate('tasks', 'counts')
  return useMutation({
    mutationFn: ({ id, text }) => api.tasks.close(id, text),
    onSuccess:  invalidate,
  })
}

export function useDeleteTask() {
  const invalidate = useInvalidate('tasks', 'counts', 'tags', 'locations')
  return useMutation({
    mutationFn: (id) => api.tasks.delete(id),
    onSuccess:  invalidate,
  })
}

export function useCreateFilter() {
  const invalidate = useInvalidate('filters')
  return useMutation({
    mutationFn: ({ name, filter }) => api.filters.create(name, filter),
    onSuccess:  invalidate,
  })
}

export function useDeleteFilter() {
  const invalidate = useInvalidate('filters')
  return useMutation({
    mutationFn: (idx) => api.filters.delete(idx),
    onSuccess:  invalidate,
  })
}
