import React from 'react';
import type { Assignment, ScenarioResponse } from '@/lib/types';
import DataTable, { Column } from '@/components/ui/DataTable';

interface RosterTableProps {
  assignments: Assignment[];
  scenario?: ScenarioResponse;
  filterShift?: string;
  filterUnit?: string;
  filterEmployee?: string;
}

export default function RosterTable({
  assignments,
  scenario,
  filterShift,
  filterUnit,
  filterEmployee,
}: RosterTableProps) {
  const getName = (id: string, list?: { id: string; name: string }[]) =>
    list?.find(x => x.id === id)?.name ?? id;

  const filtered = assignments.filter(a => {
    if (filterShift && a.shift_id !== filterShift) return false;
    if (filterUnit && a.unit_id !== filterUnit) return false;
    if (filterEmployee && a.employee_id !== filterEmployee) return false;
    return true;
  });

  const columns: Column<Assignment>[] = [
    {
      key: 'employee_id',
      header: 'Employee',
      render: (a: Assignment) => (scenario ? getName(a.employee_id, scenario.employees) : a.employee_id),
    },
    {
      key: 'unit_id',
      header: 'Production Unit',
      render: (a: Assignment) => (scenario ? getName(a.unit_id, scenario.units) : a.unit_id),
    },
    {
      key: 'shift_id',
      header: 'Shift',
      render: (a: Assignment) => (scenario ? getName(a.shift_id, scenario.shifts) : a.shift_id),
    },
    {
      key: 'hours',
      header: 'Hours',
      render: (a: Assignment) => <span className="font-mono">{a.hours.toFixed(1)}</span>,
      className: 'text-right',
    },
  ];

  return (
    <DataTable<Assignment>
      columns={columns}
      data={filtered}
      getRowKey={(a, idx) => `${a.employee_id}-${a.unit_id}-${a.shift_id}-${idx}`}
      emptyMessage="No assignments match the current filters."
    />
  );
}
