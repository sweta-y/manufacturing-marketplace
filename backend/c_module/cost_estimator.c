#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int id;
    double setup_cost;
    double setup_time;
    double time_per_unit;
    double hourly_rate;
    const char *name;
} ProcessInfo;

typedef struct {
    int id;
    double rate_per_unit;
    double multiplier;
    const char *name;
} MaterialInfo;

ProcessInfo processes[] = {
    {1, 500.0, 2.0, 0.5, 800.0, "CNC Machining"},
    {2, 100.0, 0.5, 0.75, 250.0, "3D Printing"},
    {3, 200.0, 1.0, 0.2, 500.0, "Laser Cutting"}
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
    if (argc != 5) {
        printf("{\"error\":\"Usage: cost_estimator <process_id> <material_id> <quantity> <surface_finish>\"}\n");
        return 1;
    }
    int process_id = atoi(argv[1]);
    int material_id = atoi(argv[2]);
    int quantity = atoi(argv[3]);
    const char *finish = argv[4];
    double finish_rate = 0.0;
    if (strcmp(finish, "Fine") == 0) finish_rate = 50.0;
    else if (strcmp(finish, "Ultra Fine") == 0) finish_rate = 120.0;
    else if (strcmp(finish, "Standard") != 0) {
        printf("{\"error\":\"Unknown surface finish\"}\n");
        return 1;
    }
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
    double setup_cost = p->setup_cost;
    double material_cost = quantity * m->rate_per_unit * m->multiplier;
    double machining_cost = quantity * p->time_per_unit * p->hourly_rate;
    double surface_finish_cost = quantity * finish_rate;
    double estimated_cost = setup_cost + material_cost + machining_cost + surface_finish_cost;
    double estimated_time_hours = p->setup_time + (quantity * p->time_per_unit);
    printf("{\"process_id\":%d,\"process_name\":\"%s\",\"material_id\":%d,\"material_name\":\"%s\",\"quantity\":%d,\"surface_finish\":\"%s\",\"estimated_cost\":%.2f,\"estimated_time_hours\":%.2f,\"cost_breakdown\":{\"setup_cost\":%.2f,\"material_cost\":%.2f,\"machining_cost\":%.2f,\"surface_finish_cost\":%.2f,\"estimated_total\":%.2f}}\n",
           process_id, p->name, material_id, m->name, quantity, finish, estimated_cost, estimated_time_hours,
           setup_cost, material_cost, machining_cost, surface_finish_cost, estimated_cost);
    return 0;
}
