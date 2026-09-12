#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int id;
    double setup_cost;
    double setup_time;
    double time_per_unit;
    const char *name;
} ProcessInfo;

typedef struct {
    int id;
    double rate_per_unit;
    double multiplier;
    const char *name;
} MaterialInfo;

ProcessInfo processes[] = {
    {1, 500.0, 2.0, 0.5, "CNC Machining"},
    {2, 100.0, 0.5, 0.75, "3D Printing"},
    {3, 200.0, 1.0, 0.2, "Laser Cutting"}
};
int num_processes = 3;

MaterialInfo materials[] = {
    {1, 150.0, 1.0, "Aluminum 6061"},
    {2, 220.0, 1.15, "Stainless Steel 304"},
    {3, 40.0, 0.8, "PLA Filament"},
    {4, 60.0, 0.9, "Acrylic Sheet"}
};
int num_materials = 4;

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("{\"error\":\"Usage: cost_estimator <process_id> <material_id> <quantity>\"}\n");
        return 1;
    }
    int process_id = atoi(argv[1]);
    int material_id = atoi(argv[2]);
    int quantity = atoi(argv[3]);
    if (quantity <= 0) {
        printf("{\"error\":\"quantity must be positive\"}\n");
        return 1;
    }
    ProcessInfo *p = NULL;
    for (int i = 0; i < num_processes; i++) {
        if (processes[i].id == process_id) { p = &processes[i]; break; }
    }
    MaterialInfo *m = NULL;
    for (int i = 0; i < num_materials; i++) {
        if (materials[i].id == material_id) { m = &materials[i]; break; }
    }
    if (!p) { printf("{\"error\":\"Unknown process_id %d\"}\n", process_id); return 1; }
    if (!m) { printf("{\"error\":\"Unknown material_id %d\"}\n", material_id); return 1; }
    double estimated_cost = p->setup_cost + (quantity * m->rate_per_unit * m->multiplier);
    double estimated_time_hours = p->setup_time + (quantity * p->time_per_unit);
    printf("{\"process_id\":%d,\"process_name\":\"%s\",\"material_id\":%d,\"material_name\":\"%s\",\"quantity\":%d,\"estimated_cost\":%.2f,\"estimated_time_hours\":%.2f}\n",
           process_id, p->name, material_id, m->name, quantity, estimated_cost, estimated_time_hours);
    return 0;
}
