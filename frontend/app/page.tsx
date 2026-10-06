'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';

const defaultRecipeForm = {
  title: '',
  description: '',
  ingredients: '',
  instructions: '',
  prep_time: '20',
  cook_time: '25',
  servings: '2',
  difficulty: 'Easy',
  cuisine: 'Italian',
};

type Recipe = {
  id: number;
  title: string;
  description?: string | null;
  ingredients: string;
  instructions: string;
  prep_time?: number | null;
  cook_time?: number | null;
  servings?: number | null;
  difficulty?: string | null;
  cuisine?: string | null;
  created_at: string;
  updated_at: string;
};

type Stats = {
  total_recipes: number;
  average_prep_time: number;
  average_cook_time: number;
  cuisines: Record<string, number>;
  difficulties: Record<string, number>;
};

const emptyForm = {
  title: '',
  description: '',
  ingredients: '',
  instructions: '',
  prep_time: '20',
  cook_time: '25',
  servings: '2',
  difficulty: 'Easy',
  cuisine: 'Italian',
};

export default function HomePage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState(defaultRecipeForm);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const fetchRecipes = useCallback(async () => {
    const response = await fetch(`${apiBaseUrl}/recipes/?limit=10`);
    if (!response.ok) {
      throw new Error('Unable to load recipes');
    }
    const data = await response.json();
    setRecipes(data.recipes || []);
  }, [apiBaseUrl]);

  const fetchStats = useCallback(async () => {
    const response = await fetch(`${apiBaseUrl}/recipes/stats`);
    if (!response.ok) {
      throw new Error('Unable to load stats');
    }
    const data = await response.json();
    setStats(data);
  }, [apiBaseUrl]);

  const loadData = useCallback(async () => {
    try {
      setError('');
      setIsLoading(true);
      await Promise.all([fetchRecipes(), fetchStats()]);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl, fetchRecipes, fetchStats]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openRecipe = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setIsEditing(false);
  };

  const startEdit = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setIsEditing(true);
    setForm({
      title: recipe.title,
      description: recipe.description || '',
      ingredients: recipe.ingredients,
      instructions: recipe.instructions,
      prep_time: String(recipe.prep_time ?? 20),
      cook_time: String(recipe.cook_time ?? 25),
      servings: String(recipe.servings ?? 2),
      difficulty: recipe.difficulty || 'Easy',
      cuisine: recipe.cuisine || 'Italian',
    });
  };

  const resetForm = () => {
    setForm(defaultRecipeForm);
    setIsEditing(false);
    setSelectedRecipe(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const payload = {
        ...form,
        prep_time: Number(form.prep_time),
        cook_time: Number(form.cook_time),
        servings: Number(form.servings),
      };

      const url = isEditing && selectedRecipe ? `${apiBaseUrl}/recipes/${selectedRecipe.id}` : `${apiBaseUrl}/recipes/`;
      const method = isEditing && selectedRecipe ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const payloadError = await response.json();
        throw new Error(payloadError.detail || 'Recipe save failed');
      }

      resetForm();
      await loadData();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to save recipe');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (recipeId: number) => {
    try {
      const response = await fetch(`${apiBaseUrl}/recipes/${recipeId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail || 'Delete failed');
      }

      setSelectedRecipe(null);
      await loadData();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'Unable to delete recipe');
    }
  };

  return (
    <main className="page-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Recipe API dashboard</p>
          <h1>Kitchen insights and recipe management</h1>
        </div>
        <div className="stat-grid">
          <div className="stat-card">
            <span>Total recipes</span>
            <strong>{stats?.total_recipes ?? 0}</strong>
          </div>
          <div className="stat-card">
            <span>Avg prep</span>
            <strong>{stats ? `${stats.average_prep_time} min` : '0 min'}</strong>
          </div>
          <div className="stat-card">
            <span>Avg cook</span>
            <strong>{stats ? `${stats.average_cook_time} min` : '0 min'}</strong>
          </div>
        </div>
      </section>

      <section className="content-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="panel-header form-header">
            <h2>{isEditing ? 'Edit recipe' : 'Add a recipe'}</h2>
            {isEditing || selectedRecipe ? (
              <button type="button" className="secondary-button" onClick={resetForm}>
                New recipe
              </button>
            ) : null}
          </div>

          <div className="field-grid">
            <label>
              Title
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
            </label>
            <label>
              Cuisine
              <input value={form.cuisine} onChange={(e) => setForm({ ...form, cuisine: e.target.value })} />
            </label>
            <label>
              Difficulty
              <select value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}>
                <option>Easy</option>
                <option>Medium</option>
                <option>Hard</option>
              </select>
            </label>
            <label>
              Servings
              <input type="number" min="1" value={form.servings} onChange={(e) => setForm({ ...form, servings: e.target.value })} />
            </label>
            <label>
              Prep time (min)
              <input type="number" min="0" value={form.prep_time} onChange={(e) => setForm({ ...form, prep_time: e.target.value })} />
            </label>
            <label>
              Cook time (min)
              <input type="number" min="0" value={form.cook_time} onChange={(e) => setForm({ ...form, cook_time: e.target.value })} />
            </label>
          </div>

          <label>
            Description
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
          </label>

          <label>
            Ingredients
            <textarea value={form.ingredients} onChange={(e) => setForm({ ...form, ingredients: e.target.value })} rows={4} required />
          </label>

          <label>
            Instructions
            <textarea value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} rows={5} required />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : isEditing ? 'Update recipe' : 'Create recipe'}
          </button>
        </form>

        <div className="panel list-panel">
          <div className="panel-header">
            <h2>Latest recipes</h2>
          </div>

          {selectedRecipe ? (
            <div className="detail-card">
              <div className="detail-header">
                <div>
                  <p className="detail-label">Recipe details</p>
                  <h3>{selectedRecipe.title}</h3>
                </div>
                <span>{selectedRecipe.cuisine || 'General'}</span>
              </div>

              <p className="detail-description">{selectedRecipe.description || 'No description yet.'}</p>

              <div className="detail-meta">
                <span>Difficulty: {selectedRecipe.difficulty || 'N/A'}</span>
                <span>Prep: {selectedRecipe.prep_time ?? 0} min</span>
                <span>Cook: {selectedRecipe.cook_time ?? 0} min</span>
                <span>Servings: {selectedRecipe.servings ?? 'N/A'}</span>
              </div>

              <div className="detail-section">
                <h4>Ingredients</h4>
                <p>{selectedRecipe.ingredients}</p>
              </div>

              <div className="detail-section">
                <h4>Instructions</h4>
                <p>{selectedRecipe.instructions}</p>
              </div>

              <div className="detail-actions">
                <button type="button" className="small-button alt" onClick={() => startEdit(selectedRecipe)}>
                  Update
                </button>
                <button type="button" className="small-button danger" onClick={() => handleDelete(selectedRecipe.id)}>
                  Delete
                </button>
              </div>
            </div>
          ) : isLoading ? (
            <p className="muted">Loading recipes...</p>
          ) : recipes.length === 0 ? (
            <p className="muted">No recipes found yet.</p>
          ) : (
            <div className="recipe-list">
              {recipes.map((recipe) => (
                <article key={recipe.id} className="recipe-card">
                  <div className="recipe-topline">
                    <h3>{recipe.title}</h3>
                    <span>{recipe.cuisine || 'General'}</span>
                  </div>
                  <p>{recipe.description || 'No description yet.'}</p>
                  <ul>
                    <li>Difficulty: {recipe.difficulty || 'N/A'}</li>
                    <li>Prep: {recipe.prep_time ?? 0} min</li>
                    <li>Cook: {recipe.cook_time ?? 0} min</li>
                    <li>Servings: {recipe.servings ?? 'N/A'}</li>
                  </ul>

                  <div className="recipe-actions">
                    <button type="button" className="small-button" onClick={() => openRecipe(recipe)}>
                      View
                    </button>
                    <button type="button" className="small-button alt" onClick={() => startEdit(recipe)}>
                      Edit
                    </button>
                    <button type="button" className="small-button danger" onClick={() => handleDelete(recipe.id)}>
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
